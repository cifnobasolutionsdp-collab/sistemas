"""Proceso de carga de información de cartera (lay out CSV).

El lay out se documenta en ``docs/layout_carga.md``. Cada renglón referencia
los catálogos por clave; los renglones con errores se rechazan y se reportan
con su número de línea y motivo.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime

from sqlalchemy.orm import Session

from . import models

COLUMNAS_LAYOUT = [
    "periodo",
    "folio",
    "socio",
    "producto",
    "sucursal",
    "moneda",
    "actividad",
    "localidad",
    "garantia",
    "monto_original",
    "saldo_vigente",
    "saldo_vencido",
    "dias_mora",
    "plazo_meses",
    "tasa_anual",
    "fecha_otorgamiento",
    "fecha_vencimiento",
]


def _indice_por_clave(db: Session, modelo) -> dict[str, int]:
    return {obj.clave: obj.id for obj in db.query(modelo).all()}


def _fecha(valor: str):
    return datetime.strptime(valor.strip(), "%Y-%m-%d").date()


def cargar_cartera_csv(db: Session, contenido: bytes, nombre_archivo: str) -> models.CargaInformacion:
    """Carga un archivo CSV de cartera. Reemplaza los créditos ya existentes
    del mismo periodo y folio (recarga idempotente)."""
    texto = contenido.decode("utf-8-sig")
    lector = csv.DictReader(io.StringIO(texto))

    errores: list[str] = []
    aceptados = 0
    rechazados = 0

    faltantes = [c for c in COLUMNAS_LAYOUT if c not in (lector.fieldnames or [])]
    if faltantes:
        carga = models.CargaInformacion(
            periodo="-",
            archivo=nombre_archivo,
            registros=0,
            rechazados=0,
            estatus="Fallida",
            mensaje="Columnas faltantes en el lay out: " + ", ".join(faltantes),
        )
        db.add(carga)
        db.commit()
        return carga

    catalogos = {
        "producto": _indice_por_clave(db, models.ProductoCredito),
        "sucursal": _indice_por_clave(db, models.Sucursal),
        "moneda": _indice_por_clave(db, models.Moneda),
        "actividad": _indice_por_clave(db, models.Actividad),
        "localidad": _indice_por_clave(db, models.Localidad),
        "garantia": _indice_por_clave(db, models.Garantia),
    }

    periodos_vistos: set[str] = set()
    for num_linea, fila in enumerate(lector, start=2):
        try:
            periodo = fila["periodo"].strip()
            datetime.strptime(periodo, "%Y-%m")
            folio = fila["folio"].strip()
            if not folio:
                raise ValueError("folio vacío")

            referencias = {}
            for campo in ("producto", "sucursal", "moneda", "actividad", "localidad"):
                clave = fila[campo].strip()
                if clave not in catalogos[campo]:
                    raise ValueError(f"{campo} '{clave}' no existe en el catálogo")
                referencias[campo] = catalogos[campo][clave]

            clave_garantia = (fila.get("garantia") or "").strip()
            garantia_id = None
            if clave_garantia:
                if clave_garantia not in catalogos["garantia"]:
                    raise ValueError(f"garantía '{clave_garantia}' no existe en el catálogo")
                garantia_id = catalogos["garantia"][clave_garantia]

            prestamo = models.Prestamo(
                periodo=periodo,
                folio=folio,
                socio=fila["socio"].strip(),
                producto_id=referencias["producto"],
                sucursal_id=referencias["sucursal"],
                moneda_id=referencias["moneda"],
                actividad_id=referencias["actividad"],
                localidad_id=referencias["localidad"],
                garantia_id=garantia_id,
                monto_original=float(fila["monto_original"]),
                saldo_vigente=float(fila["saldo_vigente"]),
                saldo_vencido=float(fila["saldo_vencido"]),
                dias_mora=int(float(fila["dias_mora"])),
                plazo_meses=int(float(fila["plazo_meses"])),
                tasa_anual=float(fila["tasa_anual"]),
                fecha_otorgamiento=_fecha(fila["fecha_otorgamiento"]),
                fecha_vencimiento=_fecha(fila["fecha_vencimiento"]),
            )

            if periodo not in periodos_vistos:
                periodos_vistos.add(periodo)
            db.query(models.Prestamo).filter(
                models.Prestamo.periodo == periodo, models.Prestamo.folio == folio
            ).delete()
            db.add(prestamo)
            aceptados += 1
        except (KeyError, ValueError) as exc:
            rechazados += 1
            if len(errores) < 50:
                errores.append(f"Línea {num_linea}: {exc}")

    estatus = "Exitosa" if rechazados == 0 else ("Parcial" if aceptados else "Fallida")
    carga = models.CargaInformacion(
        periodo=", ".join(sorted(periodos_vistos)) or "-",
        archivo=nombre_archivo,
        registros=aceptados,
        rechazados=rechazados,
        estatus=estatus,
        mensaje="\n".join(errores),
    )
    db.add(carga)
    db.commit()
    return carga
