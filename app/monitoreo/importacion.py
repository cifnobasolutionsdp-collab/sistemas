"""Importación de balanzas de comprobación y estados financieros.

Formatos aceptados: CSV (coma, punto y coma o tabulador), Excel ``.xlsx`` y
Excel 97-2003 ``.xls``. Ver ``docs/monitoreo_financiero.md``.
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from .mapeo import Mapeador, normalizar_cuenta
from .modelos import CargaFinanciera, Entidad, EstadoFinanciero
from .rubros import RUBROS_POR_CLAVE, agregados

PARAMETROS_PERIODO = {"inflacion", "tasa_mercado", "tasa_empresarial"}


# --------------------------------------------------------------------- lectura
def _clave_columna(texto) -> str:
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def leer_tabla(contenido: bytes, nombre: str) -> list[list[list]]:
    """Devuelve una lista de hojas; cada hoja es una lista de renglones (listas de celdas)."""
    nombre = (nombre or "").lower()
    if nombre.endswith(".xlsx") or nombre.endswith(".xlsm") or contenido[:2] == b"PK":
        from openpyxl import load_workbook

        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
        hojas = [[list(r) for r in hoja.iter_rows(values_only=True)] for hoja in libro.worksheets]
        libro.close()
        return hojas
    if nombre.endswith(".xls") or contenido[:4] == b"\xd0\xcf\x11\xe0":
        import xlrd

        libro = xlrd.open_workbook(file_contents=contenido)
        return [[hoja.row_values(i) for i in range(hoja.nrows)] for hoja in libro.sheets()]
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")
    try:
        dialecto = csv.Sniffer().sniff(texto[:4096], delimiters=",;\t|")
        delim = dialecto.delimiter
    except csv.Error:
        delim = ","
    return [[r for r in csv.reader(io.StringIO(texto), delimiter=delim)]]


def a_numero(valor) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip().replace("$", "").replace(" ", "").replace(" ", "")
    if not s or s in {"-", "NA", "N/A", "n/a"}:
        return None
    negativo = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if s.endswith("-"):
        negativo, s = True, s[:-1]
    porcentaje = s.endswith("%")
    s = s.rstrip("%")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", "") if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
    try:
        n = float(s)
    except ValueError:
        return None
    if porcentaje:
        n /= 100
    return -n if negativo else n


def _encabezado(hoja: list[list], alias: dict[str, set[str]], requeridas: set[str]):
    """Localiza el renglón de encabezado (en los primeros 30) y el índice de cada columna."""
    for i, renglon in enumerate(hoja[:30]):
        claves = [_clave_columna(c) for c in renglon]
        indices = {}
        for nombre, posibles in alias.items():
            for j, c in enumerate(claves):
                if c in posibles:
                    indices[nombre] = j
                    break
        if requeridas <= set(indices):
            return i, indices
    return None, {}


@dataclass
class ResultadoImportacion:
    estatus: str = "Exitosa"
    mensajes: list[str] = field(default_factory=list)
    renglones: int = 0
    rubros: dict[str, float] = field(default_factory=dict)
    sin_mapeo: list[tuple[str, str, float]] = field(default_factory=list)
    estado_id: int | None = None


def _estado(db: Session, entidad: Entidad, fecha_corte: date) -> EstadoFinanciero:
    estado = (
        db.query(EstadoFinanciero)
        .filter(EstadoFinanciero.entidad_id == entidad.id, EstadoFinanciero.fecha_corte == fecha_corte)
        .one_or_none()
    )
    if estado is None:
        estado = EstadoFinanciero(entidad_id=entidad.id, fecha_corte=fecha_corte, rubros="{}")
        db.add(estado)
    return estado


def _bitacora(db, entidad, fecha_corte, tipo, archivo, res: ResultadoImportacion):
    db.add(
        CargaFinanciera(
            entidad_id=entidad.id if entidad else None,
            fecha_corte=fecha_corte,
            tipo=tipo,
            archivo=archivo[:255],
            renglones=res.renglones,
            estatus=res.estatus,
            mensaje="\n".join(res.mensajes)[:20000],
        )
    )


def _validar_cuadre(res: ResultadoImportacion, datos: dict[str, float], sugerencia: str = "Revise el mapeo de cuentas.") -> None:
    ag = agregados(datos)
    if ag["activo_total"] and abs(ag["descuadre"]) > max(1.0, ag["activo_total"] * 0.001):
        res.mensajes.append(
            f"Aviso: el balance no cuadra (Activo − Pasivo − Capital = {ag['descuadre']:,.2f}). "
            + sugerencia
        )
        if res.estatus == "Exitosa":
            res.estatus = "Parcial"


# ------------------------------------------------------------ balanza
ALIAS_BALANZA = {
    "cuenta": {"cuenta", "no_cuenta", "num_cuenta", "numero_cuenta", "numero_de_cuenta", "cuenta_contable", "codigo", "clave"},
    "descripcion": {"descripcion", "nombre", "concepto", "nombre_cuenta", "nombre_de_la_cuenta"},
    "saldo_final": {"saldo_final", "saldo", "saldo_actual", "saldo_al_cierre"},
    "deudor": {"saldo_deudor", "deudor", "saldo_final_deudor", "deudora"},
    "acreedor": {"saldo_acreedor", "acreedor", "saldo_final_acreedor", "acreedora"},
    "rubro": {"rubro", "rubro_monitoreo"},
    "tipo": {"tipo", "tipo_cuenta", "nivel", "afectable"},
}

VALORES_DETALLE = {"d", "detalle", "afectable", "si", "s", "1", "true", "movimiento", "auxiliar"}


def _cuentas_acumulativas(cuentas: list[dict]) -> set[str]:
    """Identifica las cuentas acumulativas (de mayor) para no duplicar saldos.

    1. Si la balanza trae la columna ``tipo`` / ``afectable`` se respeta.
    2. Una cuenta es acumulativa si su código es prefijo de otra cuenta
       (catálogos jerárquicos: 1, 11, 1101, 110101).
    3. En catálogos de longitud fija (1101000000, 1101001000) los ceros a la
       derecha indican nivel: la cuenta es acumulativa si su código sin ceros
       finales es prefijo de otra cuenta más específica.
    """
    if any(c.get("tipo") for c in cuentas):
        return {c["cuenta"] for c in cuentas if c.get("tipo") and c["tipo"] not in VALORES_DETALLE}
    codigos = sorted({c["cuenta"] for c in cuentas})
    acum = {a for i, a in enumerate(codigos) if i + 1 < len(codigos) and codigos[i + 1].startswith(a)}
    if len({len(c) for c in codigos}) == 1:
        recortados = {c: (c.rstrip("0") or c[:1]) for c in codigos}
        for a in codigos:
            ra = recortados[a]
            if len(ra) < len(a) and any(b != a and len(recortados[b]) > len(ra) and recortados[b].startswith(ra) for b in codigos):
                acum.add(a)
    return acum


def importar_balanza(db: Session, entidad: Entidad, fecha_corte: date, contenido: bytes, archivo: str) -> ResultadoImportacion:
    res = ResultadoImportacion()
    try:
        hojas = leer_tabla(contenido, archivo)
    except Exception as exc:  # archivo ilegible
        res.estatus = "Fallida"
        res.mensajes.append(f"No fue posible leer el archivo: {exc}")
        _bitacora(db, entidad, fecha_corte, "balanza", archivo, res)
        db.commit()
        return res

    hoja, fila, idx = None, None, {}
    for h in hojas:
        fila, idx = _encabezado(h, ALIAS_BALANZA, {"cuenta"})
        if fila is not None and ("saldo_final" in idx or "deudor" in idx or "acreedor" in idx):
            hoja = h
            break
    if hoja is None:
        res.estatus = "Fallida"
        res.mensajes.append(
            "No se encontró el encabezado de la balanza. Se requiere la columna 'cuenta' y "
            "'saldo_final' (o 'saldo_deudor' / 'saldo_acreedor')."
        )
        _bitacora(db, entidad, fecha_corte, "balanza", archivo, res)
        db.commit()
        return res

    cuentas: list[dict] = []
    columnas_separadas = "deudor" in idx or "acreedor" in idx
    for n, renglon in enumerate(hoja[fila + 1 :], start=fila + 2):
        celda = lambda k: renglon[idx[k]] if k in idx and idx[k] < len(renglon) else None  # noqa: E731
        cuenta = normalizar_cuenta(celda("cuenta"))
        if not cuenta:
            continue
        if columnas_separadas:
            saldo = (a_numero(celda("deudor")) or 0.0) - (a_numero(celda("acreedor")) or 0.0)
        else:
            saldo = a_numero(celda("saldo_final"))
            if saldo is None:
                continue
        cuentas.append(
            {
                "cuenta": cuenta,
                "descripcion": str(celda("descripcion") or "").strip(),
                "saldo": saldo,
                "rubro": _clave_columna(celda("rubro")) if celda("rubro") else "",
                "tipo": _clave_columna(celda("tipo")) if celda("tipo") else "",
                "linea": n,
            }
        )
    res.renglones = len(cuentas)
    if not cuentas:
        res.estatus = "Fallida"
        res.mensajes.append("La balanza no contiene cuentas con saldo.")
        _bitacora(db, entidad, fecha_corte, "balanza", archivo, res)
        db.commit()
        return res

    acumulativas = _cuentas_acumulativas(cuentas)
    detalle = [c for c in cuentas if c["cuenta"] not in acumulativas or c["rubro"]]

    # Convención de signos: con una sola columna de saldo, si las cuentas de
    # naturaleza acreedora (2, 3, 4) vienen mayoritariamente en negativo, la
    # balanza usa saldo con signo (deudor +, acreedor −).
    if columnas_separadas:
        con_signo = True
    else:
        acreedoras = [c["saldo"] for c in detalle if c["cuenta"][:1] in "234" and c["saldo"]]
        con_signo = bool(acreedoras) and sum(1 for s in acreedoras if s < 0) > len(acreedoras) / 2

    mapeador = Mapeador(db, entidad.id)
    datos_nuevos: dict[str, float] = {}
    for c in detalle:
        rubro = c["rubro"] if c["rubro"] in RUBROS_POR_CLAVE else mapeador.rubro(c["cuenta"])
        if c["rubro"] and c["rubro"] not in RUBROS_POR_CLAVE:
            res.mensajes.append(f"Línea {c['linea']}: rubro '{c['rubro']}' no existe; se usó el mapeo de cuentas.")
        if rubro is None:
            if abs(c["saldo"]) > 0.005:
                res.sin_mapeo.append((c["cuenta"], c["descripcion"], c["saldo"]))
            continue
        r = RUBROS_POR_CLAVE[rubro]
        valor = c["saldo"] * r.signo if con_signo else c["saldo"]
        datos_nuevos[rubro] = datos_nuevos.get(rubro, 0.0) + valor

    # Balanza no cerrada: el resultado del ejercicio está en las cuentas de resultados.
    if not datos_nuevos.get("resultado_ejercicio"):
        ag = agregados(datos_nuevos)
        if ag["ingresos_totales"] or ag["gastos_totales"]:
            datos_nuevos["resultado_ejercicio"] = ag["excedente_neto"]

    if res.sin_mapeo:
        res.estatus = "Parcial"
        res.mensajes.append(
            f"{len(res.sin_mapeo)} cuenta(s) de detalle sin rubro asignado (se omitieron). "
            "Agregue reglas en 'Mapeo de cuentas' o la columna 'rubro' en la balanza:"
        )
        for cuenta, desc, saldo in res.sin_mapeo[:100]:
            res.mensajes.append(f"  {cuenta}  {desc[:60]}  {saldo:,.2f}")

    estado = _estado(db, entidad, fecha_corte)
    datos = {k: v for k, v in estado.datos().items() if RUBROS_POR_CLAVE.get(k) and RUBROS_POR_CLAVE[k].estado == "complementario"}
    datos.update(datos_nuevos)
    estado.fijar(datos)
    estado.origen = f"Balanza: {archivo}"[:200]
    _validar_cuadre(res, datos)
    res.rubros = datos
    res.mensajes.insert(
        0,
        f"{len(detalle)} cuentas de detalle procesadas ({len(acumulativas)} acumulativas omitidas); "
        f"convención de saldos: {'con signo (deudor +, acreedor −)' if con_signo else 'según naturaleza'}.",
    )
    _bitacora(db, entidad, fecha_corte, "balanza", archivo, res)
    db.commit()
    res.estado_id = estado.id
    return res


# ------------------------------------------------------------ estados financieros
ALIAS_ESTADOS = {
    "clave": {"clave", "rubro", "clave_rubro", "codigo"},
    "importe": {"importe", "monto", "saldo", "valor", "importe_mxn"},
}


def importar_estados(db: Session, entidad: Entidad, fecha_corte: date, contenido: bytes, archivo: str) -> ResultadoImportacion:
    """Importa el lay out de estados financieros (clave de rubro + importe).

    Puede contener sólo una parte (por ejemplo, únicamente datos
    complementarios); los rubros no incluidos conservan su valor anterior.
    """
    res = ResultadoImportacion()
    try:
        hojas = leer_tabla(contenido, archivo)
    except Exception as exc:
        res.estatus = "Fallida"
        res.mensajes.append(f"No fue posible leer el archivo: {exc}")
        _bitacora(db, entidad, fecha_corte, "estados", archivo, res)
        db.commit()
        return res

    nuevos: dict[str, float] = {}
    parametros: dict[str, float] = {}
    for hoja in hojas:
        fila, idx = _encabezado(hoja, ALIAS_ESTADOS, {"clave", "importe"})
        if fila is None:
            continue
        for n, renglon in enumerate(hoja[fila + 1 :], start=fila + 2):
            if idx["clave"] >= len(renglon):
                continue
            clave = _clave_columna(renglon[idx["clave"]])
            if not clave:
                continue
            valor = a_numero(renglon[idx["importe"]] if idx["importe"] < len(renglon) else None)
            if valor is None:
                continue
            if clave in PARAMETROS_PERIODO:
                parametros[clave] = valor / 100 if abs(valor) > 1 else valor
            elif clave in RUBROS_POR_CLAVE:
                nuevos[clave] = nuevos.get(clave, 0.0) + valor
                res.renglones += 1
            else:
                res.mensajes.append(f"Línea {n}: clave '{clave}' no reconocida (omitida).")
    if not nuevos and not parametros:
        res.estatus = "Fallida"
        res.mensajes.append("No se encontraron renglones con columnas 'clave' e 'importe'.")
        _bitacora(db, entidad, fecha_corte, "estados", archivo, res)
        db.commit()
        return res
    if any(m.startswith("Línea") for m in res.mensajes):
        res.estatus = "Parcial"

    estado = _estado(db, entidad, fecha_corte)
    datos = estado.datos()
    datos.update(nuevos)
    estado.fijar(datos)
    for k, v in parametros.items():
        setattr(estado, k, v)
    solo_complementarios = all(RUBROS_POR_CLAVE[k].estado == "complementario" for k in nuevos)
    if solo_complementarios and estado.origen:
        estado.origen = f"{estado.origen.split(' + ')[0]} + complementarios: {archivo}"[:200]
    else:
        estado.origen = f"Estados financieros: {archivo}"[:200]
    if any(RUBROS_POR_CLAVE[k].estado == "balance" for k in nuevos):
        _validar_cuadre(res, datos, "Revise los importes capturados.")
    res.rubros = datos
    res.mensajes.insert(0, f"{res.renglones} rubros y {len(parametros)} parámetros importados.")
    _bitacora(db, entidad, fecha_corte, "estados", archivo, res)
    db.commit()
    res.estado_id = estado.id
    return res
