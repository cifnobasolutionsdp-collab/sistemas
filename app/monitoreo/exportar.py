"""Exportación a Excel del monitoreo y generación de plantillas de importación."""
from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .estrategias import plan_de_accion
from .indicadores import GRUPOS
from .mapeo import REGLAS_POR_OMISION
from .rubros import ESTADOS, RUBROS, rubros_de

AZUL = PatternFill("solid", fgColor="14406E")
GRIS = PatternFill("solid", fgColor="EAEFF5")
COLOR_ESTATUS = {
    "cumple": PatternFill("solid", fgColor="D5EFE5"),
    "alerta": PatternFill("solid", fgColor="F7EDD8"),
    "deficiente": PatternFill("solid", fgColor="F6D5D0"),
}
ETIQUETA_ESTATUS = {"cumple": "Cumple", "alerta": "Alerta", "deficiente": "Deficiente", "informativo": "Informativo", "na": "N/A"}
BLANCO = Font(color="FFFFFF", bold=True)


def formato_valor(fila) -> str:
    v = fila["valor"]
    if v is None:
        return "N/A"
    fmt = fila["ind"].formato
    if fmt == "sino":
        return "Sí" if v >= 1 else "No"
    if fmt == "veces":
        return f"{v:,.2f} x"
    return f"{v * 100:,.2f} %"


def _encabezado(ws, fila, valores):
    for j, v in enumerate(valores, start=1):
        c = ws.cell(row=fila, column=j, value=v)
        c.fill = AZUL
        c.font = BLANCO
        c.alignment = Alignment(wrap_text=True, vertical="center")


def _anchos(ws, anchos):
    for j, a in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(j)].width = a


def exportar_monitoreo(entidad, resultados: list[tuple]) -> bytes:
    """``resultados``: lista de (estado, resultado) ordenada por fecha; el último es el periodo evaluado."""
    wb = Workbook()
    estado, actual = resultados[-1]
    ws = wb.active
    ws.title = "Indicadores"
    ws["A1"] = f"SISTEMA DE EVALUACIÓN Y MONITOREO FINANCIERO — {entidad.nombre} ({entidad.tipo})"
    ws["A1"].font = Font(bold=True, size=13, color="14406E")
    ws["A2"] = (
        f"Al {estado.fecha_corte:%d/%m/%Y}: {len(actual['deficientes'])} de {actual['evaluados']} indicadores "
        f"evaluados son deficientes ({actual['pct_deficientes'] * 100:.0f} %) y {len(actual['alertas'])} están en alerta."
    )
    cab = ["Código", "Indicador", "Meta"] + [e.fecha_corte.strftime("%d/%m/%Y") for e, _ in resultados] + ["Estatus", "Ajuste requerido ($)"]
    _encabezado(ws, 4, cab)
    r = 5
    grupo = None
    for fila in actual["filas"]:
        ind = fila["ind"]
        if ind.grupo != grupo:
            grupo = ind.grupo
            ws.cell(row=r, column=1, value=f"{grupo} — {GRUPOS[grupo]}").font = Font(bold=True, color="14406E")
            for j in range(1, len(cab) + 1):
                ws.cell(row=r, column=j).fill = GRIS
            r += 1
        ws.cell(row=r, column=1, value=ind.codigo)
        ws.cell(row=r, column=2, value=ind.nombre)
        ws.cell(row=r, column=3, value=ind.meta)
        for j, (_, res) in enumerate(resultados, start=4):
            ws.cell(row=r, column=j, value=formato_valor(res["por_codigo"][ind.codigo])).alignment = Alignment(horizontal="right")
        c = ws.cell(row=r, column=4 + len(resultados), value=ETIQUETA_ESTATUS[fila["estatus"]])
        if fila["estatus"] in COLOR_ESTATUS:
            c.fill = COLOR_ESTATUS[fila["estatus"]]
        if fila["brecha"] is not None:
            ws.cell(row=r, column=5 + len(resultados), value=round(fila["brecha"], 2)).number_format = "#,##0.00"
        r += 1
    _anchos(ws, [9, 52, 26] + [13] * len(resultados) + [13, 18])
    ws.freeze_panes = "D5"

    # Plan de acción
    wp = wb.create_sheet("Plan de acción")
    _encabezado(wp, 1, ["Prioridad", "Código", "Indicador", "Valor", "Meta", "Estatus", "Causas probables (fuera de meta)", "Indicadores que arrastra", "Estrategias recomendadas"])
    r = 2
    for p in plan_de_accion(actual):
        f = p["fila"]
        valores = [
            p["prioridad"], p["codigo"], f["ind"].nombre, formato_valor(f), f["ind"].meta, ETIQUETA_ESTATUS[f["estatus"]],
            ", ".join(p["causas"]) or "—", ", ".join(p["arrastra"]) or "—",
            "\n".join(f"{i}. {e}" for i, e in enumerate(p["estrategias"], start=1)),
        ]
        for j, v in enumerate(valores, start=1):
            c = wp.cell(row=r, column=j, value=v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        wp.cell(row=r, column=6).fill = COLOR_ESTATUS.get(f["estatus"], GRIS)
        r += 1
    _anchos(wp, [11, 8, 38, 12, 18, 12, 24, 22, 110])

    # IFRS 9
    wi = wb.create_sheet("IFRS 9")
    pce = actual["pce"]
    wi["A1"] = "Pérdida crediticia esperada (PCE) — IFRS 9"
    wi["A1"].font = Font(bold=True, size=12, color="14406E")
    wi["A2"] = f"Fuente de la PCE: {pce['fuente_pce']}. Factor prospectivo ponderado: {pce['factor']:.4f}. LGD: {pce['lgd'] * 100:.1f} %"
    _encabezado(wi, 4, ["Etapa", "Cartera", "Participación", "PD ajustada", "PCE", "Reserva constituida", "Cobertura", "Suficiencia", "Déficit"])
    for i, e in enumerate(pce["etapas"], start=5):
        vals = [e["etapa"], e["cartera"], e["participacion"], e["pd"], e["pce"], e["reserva"], e["cobertura"], e["suficiencia"], e["deficit"]]
        for j, v in enumerate(vals, start=1):
            c = wi.cell(row=i, column=j, value=v)
            c.number_format = "0.00%" if j in (3, 4, 7, 8) else "#,##0.00"
    t = 8
    for j, v in enumerate(["Total", pce["cartera_total"], 1 if pce["cartera_total"] else None, None, pce["pce_total"], pce["reserva_total"], None, pce["suficiencia"], pce["deficit"]], start=1):
        c = wi.cell(row=t, column=j, value=v)
        c.font = Font(bold=True)
        c.number_format = "0.00%" if j in (3, 8) else "#,##0.00"
    _encabezado(wi, 10, ["Escenario", "Peso", "Factor PD", "PCE", "Déficit vs. reserva"])
    for i, e in enumerate(pce["escenarios"], start=11):
        for j, v in enumerate([e["nombre"], e["peso"], e["factor"], e["pce"], e["deficit"]], start=1):
            c = wi.cell(row=i, column=j, value=v)
            c.number_format = "0.00%" if j == 2 else ("0.00" if j == 3 else "#,##0.00")
    _anchos(wi, [12, 18, 14, 14, 18, 20, 12, 12, 16])

    # Rubros
    wr = wb.create_sheet("Rubros")
    _encabezado(wr, 1, ["Estado", "Clave", "Concepto"] + [e.fecha_corte.strftime("%d/%m/%Y") for e, _ in resultados])
    datos = [e.datos() for e, _ in resultados]
    for i, rb in enumerate(RUBROS, start=2):
        wr.cell(row=i, column=1, value=ESTADOS[rb.estado])
        wr.cell(row=i, column=2, value=rb.clave)
        wr.cell(row=i, column=3, value=rb.concepto)
        for j, d in enumerate(datos, start=4):
            if rb.clave in d:
                wr.cell(row=i, column=j, value=d[rb.clave]).number_format = "#,##0.00"
    _anchos(wr, [22, 26, 60] + [16] * len(resultados))

    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


def plantilla_estados() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Instrucciones"
    lineas = [
        "LAY OUT DE ESTADOS FINANCIEROS — Sistema de Evaluación y Monitoreo Financiero",
        "",
        "1. Capture los importes en las hojas 'Balance General', 'Estado de Resultados' y 'Datos complementarios'.",
        "2. No modifique la columna 'clave'. Puede dejar en blanco los rubros que no apliquen.",
        "3. Importes en pesos y en positivo según su naturaleza (las estimaciones también en positivo).",
        "   Sólo el resultado del ejercicio puede ser negativo (pérdida).",
        "4. El Estado de Resultados es ACUMULADO del 1 de enero a la fecha de corte; el sistema lo anualiza.",
        "5. En 'Datos complementarios' capture la morosidad por antigüedad, castigos, reservas y PCE por etapa",
        "   (IFRS 9), número de socios y los parámetros del periodo: inflación, tasa de mercado y tasa empresarial",
        "   (en porcentaje anual, p. ej. 4.5).",
        "6. Puede importar este archivo completo o sólo la hoja de datos complementarios después de importar la balanza.",
    ]
    for i, t in enumerate(lineas, start=1):
        ws.cell(row=i, column=1, value=t)
    ws["A1"].font = Font(bold=True, size=13, color="14406E")
    ws.column_dimensions["A"].width = 110
    for estado, titulo in ESTADOS.items():
        h = wb.create_sheet(titulo)
        _encabezado(h, 1, ["clave", "concepto", "seccion", "importe"])
        fila = 2
        for rb in rubros_de(estado):
            h.cell(row=fila, column=1, value=rb.clave)
            h.cell(row=fila, column=2, value=rb.concepto)
            h.cell(row=fila, column=3, value=rb.seccion)
            h.cell(row=fila, column=4).number_format = "#,##0.00"
            fila += 1
        if estado == "complementario":
            for clave, concepto in [
                ("inflacion", "Inflación anual del periodo (%)"),
                ("tasa_mercado", "Tasa de mercado de referencia, p. ej. CETES 28 días (%)"),
                ("tasa_empresarial", "Tasa activa empresarial objetivo (%)"),
            ]:
                h.cell(row=fila, column=1, value=clave)
                h.cell(row=fila, column=2, value=concepto)
                h.cell(row=fila, column=3, value="Parámetros")
                fila += 1
        _anchos(h, [28, 70, 14, 20])
    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


def plantilla_balanza() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Balanza"
    _encabezado(ws, 1, ["cuenta", "descripcion", "saldo_inicial", "cargos", "abonos", "saldo_final", "rubro"])
    for i, (prefijo, rubro, desc) in enumerate(REGLAS_POR_OMISION, start=2):
        ws.cell(row=i, column=1, value=prefijo.ljust(4, "0") + "01")
        ws.cell(row=i, column=2, value=desc)
    _anchos(ws, [14, 55, 16, 16, 16, 16, 26])
    wi = wb.create_sheet("Instrucciones")
    for i, t in enumerate([
        "BALANZA DE COMPROBACIÓN — instrucciones",
        "",
        "• Columnas obligatorias: 'cuenta' y 'saldo_final' (o bien 'saldo_deudor' y 'saldo_acreedor').",
        "• Se aceptan balanzas con cuentas de mayor y subcuentas: el sistema sólo suma las cuentas de detalle.",
        "• Saldos: positivos según su naturaleza, o con signo (deudor +, acreedor −); el sistema detecta la convención.",
        "• Columna opcional 'rubro': asigna la cuenta a un rubro sin depender del mapeo por prefijo.",
        "• El mapeo por prefijo se administra en Evaluación y Monitoreo Financiero → Mapeo de cuentas (general o por entidad).",
        "• La morosidad por antigüedad, castigos, reservas por etapa y número de socios no vienen en la balanza:",
        "  captúrelos en la hoja 'Datos complementarios' del lay out de estados financieros.",
    ], start=1):
        wi.cell(row=i, column=1, value=t)
    wi.column_dimensions["A"].width = 110
    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()
