"""Cálculo y evaluación de indicadores PERLAS (WOCCU) e IFRS 9.

Los valores se expresan como fracción decimal (0.10 = 10 %), salvo los
indicadores en "veces". Los indicadores de rendimientos y costos (R) se
anualizan con base en los meses transcurridos del ejercicio y se dividen
entre el saldo promedio; las señales expansivas (S) son crecimientos
anualizados contra el cierre del ejercicio anterior (o el periodo previo
disponible).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from .ifrs9 import calcular_pce
from .modelos import Entidad, EstadoFinanciero, MetaIndicador
from .rubros import agregados

GRUPOS = {
    "P": "Protección",
    "E": "Estructura financiera",
    "R": "Rendimientos y costos (anualizados)",
    "L": "Liquidez",
    "A": "Activos improductivos",
    "S": "Señales expansivas (crecimiento anualizado)",
    "I": "IFRS 9 — Pérdida crediticia esperada",
    "K": "Solvencia y eficiencia",
}

TOLERANCIA = 0.10  # margen relativo para el estatus "Alerta"


@dataclass
class Contexto:
    entidad: Entidad
    estado: EstadoFinanciero
    d: dict[str, float]  # rubros actuales
    a: dict[str, float]  # agregados actuales
    p: dict[str, float]  # promedio de agregados + rubros del ejercicio
    factor: float  # anualización de flujos
    base: dict[str, float] | None  # agregados + rubros del periodo base de crecimiento
    meses_crec: float | None
    anterior: dict[str, float] | None  # agregados + rubros del periodo inmediato anterior
    pce: dict
    valores: dict[str, float | None] = field(default_factory=dict)

    def g(self, clave: str) -> float:
        return float(self.d.get(clave) or self.a.get(clave) or 0.0)

    def tiene(self, clave: str) -> bool:
        return clave in self.d

    def prom(self, clave: str) -> float:
        return float(self.p.get(clave) or 0.0)

    @property
    def inflacion(self):
        return self.estado.inflacion


@dataclass
class Indicador:
    codigo: str
    nombre: str
    formula: str
    meta: str
    calc: Callable[[Contexto], tuple]  # -> (valor, numerador, denominador) o (None, motivo)
    tipo: str = "min"  # min | max | rango | info | sino | custom
    limites: dict = field(default_factory=dict)  # {"SOCAP": (min, max), "SOFOM": (min, max)}
    limites_dinamicos: Callable[[Contexto], tuple] | None = None
    custom: Callable[[Contexto, float], str] | None = None
    formato: str = "pct"  # pct | veces | sino
    aplica: tuple = ("SOCAP", "SOFOM")

    @property
    def grupo(self) -> str:
        return self.codigo[0]


def _div(n: float, d: float):
    return (n / d, n, d) if d else (None, "Denominador en cero")


def _crec(ctx: Contexto, clave: str):
    if not ctx.base or not ctx.meses_crec:
        return (None, "Requiere un periodo anterior cargado")
    actual, previo = ctx.a.get(clave, 0.0), ctx.base.get(clave, 0.0)
    if previo <= 0 or actual <= 0:
        return (None, "Saldo base en cero")
    return (((actual / previo) ** (12 / ctx.meses_crec)) - 1, actual, previo)


def _requiere(ctx: Contexto, *claves: str):
    faltan = [c for c in claves if not ctx.tiene(c)]
    return f"Requiere dato complementario: {', '.join(faltan)}" if faltan else None


def _p1(ctx):
    if m := _requiere(ctx, "mora_mas_12"):
        return (None, m)
    m12 = ctx.g("mora_mas_12")
    if m12 <= 0:
        return (None, "Sin morosidad mayor a 12 meses")
    return (min(ctx.g("estimaciones"), m12) / m12, min(ctx.g("estimaciones"), m12), m12)


def _p2(ctx):
    if m := _requiere(ctx, "mora_1_12", "mora_mas_12"):
        return (None, m)
    m112 = ctx.g("mora_1_12")
    netas = ctx.g("estimaciones") - min(ctx.g("estimaciones"), ctx.g("mora_mas_12"))
    return _div(netas, m112) if m112 > 0 else (None, "Sin morosidad de 1 a 12 meses")


def _p3(ctx):
    if m := _requiere(ctx, "mora_mas_12"):
        return (None, m)
    return (1.0 if ctx.g("mora_mas_12") <= 0 else 0.0, None, None)


def _p6(ctx):
    a = ctx.a
    num = (
        a["activo_total"] + ctx.g("estimaciones") - ctx.g("mora_mas_12") - 0.35 * ctx.g("mora_1_12")
        - a["pasivo_total"] - ctx.g("activos_problematicos") + a["depositos"]
    )
    return _div(num, a["depositos"] + ctx.g("capital_social"))


def _capital_e8(ctx):
    return ctx.a["capital_contable"] if ctx.entidad.tipo == "SOFOM" else ctx.a["capital_institucional"]


def _capital_neto(ctx):
    return _capital_e8(ctx) + ctx.g("estimaciones") - ctx.g("mora_mas_12") - 0.35 * ctx.g("mora_1_12") - ctx.g("activos_problematicos")


def _flujo(ctx, clave: str, saldo: str):
    return _div(ctx.g(clave) * ctx.factor, ctx.prom(saldo))


def _r12_custom(ctx, valor):
    if valor <= 0:
        return "deficiente"
    e8, s8, s11 = ctx.valores.get("E8"), ctx.valores.get("S8"), ctx.valores.get("S11")
    if e8 is not None and e8 < 0.10 and s8 is not None and s11 is not None and s8 < s11:
        return "alerta"
    return "cumple"


def _r10_custom(ctx, valor):
    suf = ctx.pce.get("suficiencia")
    if suf is None:
        return "informativo"
    return "cumple" if suf >= 1 else ("alerta" if suf >= 1 - TOLERANCIA else "deficiente")


def _etapa(ctx, i):
    e = ctx.pce["etapas"][i]
    return (e["participacion"], e["cartera"], ctx.pce["cartera_total"]) if ctx.pce["cartera_total"] else (None, "Sin cartera")


def _suf(ctx, i):
    e = ctx.pce["etapas"][i]
    if not e["pce"]:
        return (None, "Sin pérdida esperada en la etapa")
    return (e["suficiencia"], e["reserva"], e["pce"])


def _i10(ctx):
    if not ctx.anterior:
        return (None, "Requiere un periodo anterior cargado")
    def pct(x):
        tot = x.get("cartera_etapa1", 0) + x.get("cartera_etapa2", 0) + x.get("cartera_etapa3", 0)
        return (x.get("cartera_etapa2", 0) + x.get("cartera_etapa3", 0)) / tot if tot else None
    act, ant = pct({**ctx.d}), pct(ctx.anterior)
    if act is None or ant is None:
        return (None, "Sin cartera por etapas")
    return (act - ant, None, None)


def _i11(ctx):
    return _div(_capital_e8(ctx) - ctx.pce["deficit"], ctx.a["activo_total"])


SOCAP = ("SOCAP",)

INDICADORES: list[Indicador] = [
    # ------------------------------------------------------------------ P
    Indicador("P1", "Estimaciones / Morosidad > 12 meses", "min(EPRC, mora>12) ÷ mora>12", "100 %", _p1, "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("P2", "Estimaciones netas / Morosidad 1-12 meses", "(EPRC − cobertura de mora>12) ÷ mora 1-12", "≥ 35 %", _p2, "min", {"SOCAP": (0.35, None), "SOFOM": (0.35, None)}),
    Indicador("P3", "Depuración completa de morosidad > 12 meses", "¿Cartera morosa > 12 meses = 0?", "Sí", _p3, "sino", formato="sino"),
    Indicador("P4", "Depuraciones anuales / Cartera promedio", "Castigos del ejercicio anualizados ÷ cartera bruta promedio", "Lo mínimo",
              lambda c: _div(c.g("castigos_ejercicio") * c.factor, c.prom("cartera_bruta")) if c.tiene("castigos_ejercicio") else (None, "Requiere dato complementario: castigos_ejercicio"), "info"),
    Indicador("P5", "Recuperación cartera depurada / Depuraciones acumuladas", "Recuperaciones acumuladas ÷ castigos acumulados", "> 75 %",
              lambda c: _div(c.g("recuperaciones_acumuladas"), c.g("castigos_acumulados")) if c.g("castigos_acumulados") else (None, "Sin castigos acumulados"), "min", {"SOCAP": (0.75, None), "SOFOM": (0.75, None)}),
    Indicador("P6", "Solvencia", "(Activo + EPRC − mora>12 − 35 % mora 1-12 − pasivo − activos problemáticos + depósitos) ÷ (depósitos + aportaciones)", "≥ 111 %", _p6, "min", {"SOCAP": (1.11, None)}, aplica=SOCAP),
    # ------------------------------------------------------------------ E
    Indicador("E1", "Préstamos netos / Activo total", "Cartera neta ÷ activo total", "70 % – 80 %", lambda c: _div(c.a["cartera_neta"], c.a["activo_total"]), "rango", {"SOCAP": (0.70, 0.80), "SOFOM": (0.70, 0.95)}),
    Indicador("E2", "Inversiones líquidas / Activo total", "(Disponibilidades + inversiones CP) ÷ activo total", "≤ 16 %", lambda c: _div(c.a["inversiones_liquidas"], c.a["activo_total"]), "max", {"SOCAP": (None, 0.16), "SOFOM": (None, 0.16)}),
    Indicador("E3", "Inversiones financieras / Activo total", "Inversiones LP ÷ activo total", "≤ 2 %", lambda c: _div(c.g("inversiones_lp"), c.a["activo_total"]), "max", {"SOCAP": (None, 0.02), "SOFOM": (None, 0.02)}),
    Indicador("E4", "Inversiones no financieras / Activo total", "Inversiones permanentes ÷ activo total", "0 %", lambda c: _div(c.g("inversiones_permanentes"), c.a["activo_total"]), "max", {"SOCAP": (None, 0.0), "SOFOM": (None, 0.0)}),
    Indicador("E5", "Depósitos de ahorro / Activo total", "Depósitos ÷ activo total", "70 % – 80 %", lambda c: _div(c.a["depositos"], c.a["activo_total"]), "rango", {"SOCAP": (0.70, 0.80)}, aplica=SOCAP),
    Indicador("E6", "Crédito externo / Activo total", "Préstamos bancarios ÷ activo total", "0 % – 5 %", lambda c: _div(c.g("prestamos_bancarios"), c.a["activo_total"]), "rango", {"SOCAP": (0.0, 0.05), "SOFOM": (None, None)}),
    Indicador("E7", "Aportaciones / Activo total", "Capital social ÷ activo total", "10 % – 20 %", lambda c: _div(c.g("capital_social"), c.a["activo_total"]), "rango", {"SOCAP": (0.10, 0.20)}, aplica=SOCAP),
    Indicador("E8", "Capital institucional / Activo total", "Reservas + resultados ÷ activo total (SOFOM: capital contable)", "≥ 10 %", lambda c: _div(_capital_e8(c), c.a["activo_total"]), "min", {"SOCAP": (0.10, None), "SOFOM": (0.10, None)}),
    Indicador("E9", "Capital institucional neto / Activo total", "(Capital institucional + EPRC − mora>12 − 35 % mora 1-12 − activos problemáticos) ÷ activo", "≥ 10 %", lambda c: _div(_capital_neto(c), c.a["activo_total"]), "min", {"SOCAP": (0.10, None), "SOFOM": (0.10, None)}),
    # ------------------------------------------------------------------ R
    Indicador("R1", "Ingresos por préstamos / Promedio préstamos netos", "Intereses de cartera anualizados ÷ cartera neta promedio", "≥ Tasa empresarial", lambda c: _flujo(c, "ing_intereses_cartera", "cartera_neta"), "min",
              limites_dinamicos=lambda c: (c.estado.tasa_empresarial, None)),
    Indicador("R2", "Ingresos por inv. líquidas / Promedio inv. líquidas", "Ingresos de disponibilidades anualizados ÷ inversiones líquidas promedio", "≥ Tasa de mercado", lambda c: _flujo(c, "ing_disponibilidades", "inversiones_liquidas"), "min",
              limites_dinamicos=lambda c: (c.estado.tasa_mercado, None)),
    Indicador("R3", "Ingresos por inv. financieras / Promedio inv. financieras", "Ingresos de inversiones LP anualizados ÷ inversiones LP promedio", "≥ Tasa de mercado", lambda c: _flujo(c, "ing_inversiones_lp", "inversiones_lp"), "min",
              limites_dinamicos=lambda c: (c.estado.tasa_mercado, None)),
    Indicador("R4", "Ingresos por inv. no financieras / Promedio inv. no financieras", "Ingresos de inv. permanentes anualizados ÷ promedio", "≥ R1", lambda c: _flujo(c, "ing_inversiones_permanentes", "inversiones_permanentes"), "min",
              limites_dinamicos=lambda c: (c.valores.get("R1"), None)),
    Indicador("R5", "Costo financiero: depósitos / Promedio depósitos", "Intereses de depósitos anualizados ÷ depósitos promedio", "≥ Inflación (tasa real positiva)", lambda c: _flujo(c, "int_depositos", "depositos"), "min",
              limites_dinamicos=lambda c: (c.inflacion, None), aplica=SOCAP),
    Indicador("R6", "Costo financiero: crédito externo / Promedio crédito externo", "Intereses de préstamos bancarios anualizados ÷ promedio", "≥ R5 (SOFOM: ≤ R1)", lambda c: _flujo(c, "int_prestamos_bancarios", "prestamos_bancarios"), "rango",
              limites_dinamicos=lambda c: (None, c.valores.get("R1")) if c.entidad.tipo == "SOFOM" else (c.valores.get("R5"), None)),
    Indicador("R7", "Costo financiero: aportaciones / Promedio aportaciones", "Rendimientos de aportaciones anualizados ÷ capital social promedio", "≤ R5", lambda c: _flujo(c, "int_aportaciones", "capital_social"), "max",
              limites_dinamicos=lambda c: (None, c.valores.get("R5")), aplica=SOCAP),
    Indicador("R8", "Margen bruto / Promedio activos", "Margen financiero anualizado ÷ activo promedio", "≥ R9 + R10", lambda c: _flujo(c, "margen_bruto", "activo_total"), "min",
              limites_dinamicos=lambda c: ((c.valores.get("R9") or 0) + (c.valores.get("R10") or 0), None)),
    Indicador("R9", "Gastos operativos / Promedio activos", "Gastos de administración anualizados ÷ activo promedio", "3 % – 10 %", lambda c: _flujo(c, "gastos_administracion", "activo_total"), "rango", {"SOCAP": (0.03, 0.10), "SOFOM": (0.03, 0.10)}),
    Indicador("R10", "Provisiones activos de riesgo / Promedio activos", "Estimaciones del ejercicio anualizadas ÷ activo promedio", "Suficiente para cubrir la PCE (IFRS 9)", lambda c: _flujo(c, "provisiones", "activo_total"), "custom", custom=_r10_custom),
    Indicador("R11", "Otros ingresos o gastos / Promedio activos", "(Otros ingresos − otros gastos) anualizados ÷ activo promedio", "Lo mínimo", lambda c: _flujo(c, "otros_neto", "activo_total"), "info"),
    Indicador("R12", "Excedente neto / Promedio activos (ROA)", "Resultado neto anualizado ÷ activo promedio", "> 0 y suficiente para alcanzar E8", lambda c: _flujo(c, "excedente_neto", "activo_total"), "custom", custom=_r12_custom),
    Indicador("R13", "Excedente neto / Promedio capital institucional (ROC)", "Resultado neto anualizado ÷ capital institucional promedio", "> Inflación", lambda c: _flujo(c, "excedente_neto", "capital_institucional"), "min",
              limites_dinamicos=lambda c: (c.inflacion, None)),
    # ------------------------------------------------------------------ L
    Indicador("L1", "(Inv. líquidas − CxP ≤ 30 días) / Depósitos de ahorro", "(Inversiones líquidas − CxP ≤ 30 días) ÷ depósitos", "≥ 15 %", lambda c: _div(c.a["inversiones_liquidas"] - c.g("cxp_30_dias"), c.a["depositos"]), "min", {"SOCAP": (0.15, None)}, aplica=SOCAP),
    Indicador("L2", "Reservas de liquidez / Depósitos", "Reserva de liquidez ÷ depósitos", "≥ 10 %", lambda c: _div(c.g("reserva_liquidez"), c.a["depositos"]) if c.tiene("reserva_liquidez") else (None, "Requiere dato complementario: reserva_liquidez"), "min", {"SOCAP": (0.10, None)}, aplica=SOCAP),
    Indicador("L3", "Liquidez ociosa / Activo total", "Caja sin rendimiento ÷ activo total", "< 1 %", lambda c: _div(c.g("caja"), c.a["activo_total"]), "max", {"SOCAP": (None, 0.01), "SOFOM": (None, 0.01)}),
    # ------------------------------------------------------------------ A
    Indicador("A1", "Morosidad total / Cartera bruta", "Cartera morosa (o etapa 3) ÷ cartera bruta", "≤ 5 %", lambda c: _div(c.a["morosidad_total"], c.a["cartera_bruta"]), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("A2", "Activo improductivo / Activo total", "(Caja + CxC + adjudicados + activo fijo + otros) ÷ activo total", "≤ 5 %", lambda c: _div(c.a["activo_improductivo"], c.a["activo_total"]), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("A3", "Fondos sin costo neto / Activo improductivo", "(Capital institucional + pasivos sin costo) ÷ activo improductivo", "≥ 200 %", lambda c: _div(c.a["capital_institucional"] + c.a["pasivo_sin_costo"], c.a["activo_improductivo"]), "min", {"SOCAP": (2.0, None), "SOFOM": (2.0, None)}),
    # ------------------------------------------------------------------ S
    Indicador("S1", "Crecimiento cartera neta de préstamos", "Crecimiento anualizado", "≥ Inflación (para alcanzar E1)", lambda c: _crec(c, "cartera_neta"), "min", limites_dinamicos=lambda c: (c.inflacion, None)),
    Indicador("S2", "Crecimiento inversiones líquidas", "Crecimiento anualizado", "Congruente con E2", lambda c: _crec(c, "inversiones_liquidas"), "info"),
    Indicador("S3", "Crecimiento inversiones financieras", "Crecimiento anualizado", "Congruente con E3", lambda c: _crec(c, "inversiones_lp"), "info"),
    Indicador("S4", "Crecimiento inversiones no financieras", "Crecimiento anualizado", "Congruente con E4", lambda c: _crec(c, "inversiones_permanentes"), "info"),
    Indicador("S5", "Crecimiento depósitos de ahorro", "Crecimiento anualizado", "≥ Inflación (para alcanzar E5)", lambda c: _crec(c, "depositos"), "min", limites_dinamicos=lambda c: (c.inflacion, None), aplica=SOCAP),
    Indicador("S6", "Crecimiento crédito externo", "Crecimiento anualizado", "Congruente con E6", lambda c: _crec(c, "prestamos_bancarios"), "info"),
    Indicador("S7", "Crecimiento aportaciones", "Crecimiento anualizado", "≥ Inflación (para alcanzar E7)", lambda c: _crec(c, "capital_social"), "min", limites_dinamicos=lambda c: (c.inflacion, None), aplica=SOCAP),
    Indicador("S8", "Crecimiento capital institucional", "Crecimiento anualizado", "≥ crecimiento del activo (S11)", lambda c: _crec(c, "capital_institucional"), "min", limites_dinamicos=lambda c: (c.valores.get("S11"), None)),
    Indicador("S9", "Crecimiento capital institucional neto", "Crecimiento anualizado", "Congruente con E9", lambda c: _crec(c, "capital_neto"), "info"),
    Indicador("S10", "Crecimiento de asociados", "Crecimiento anualizado", "≥ Inflación", lambda c: _crec(c, "asociados"), "min", limites_dinamicos=lambda c: (c.inflacion, None)),
    Indicador("S11", "Crecimiento activo total", "Crecimiento anualizado", "≥ Inflación", lambda c: _crec(c, "activo_total"), "min", limites_dinamicos=lambda c: (c.inflacion, None)),
    # ------------------------------------------------------------------ I (IFRS 9)
    Indicador("I1", "Cartera etapa 1 / Cartera bruta", "Cartera etapa 1 ÷ cartera total", "≥ 90 %", lambda c: _etapa(c, 0), "min", {"SOCAP": (0.90, None), "SOFOM": (0.90, None)}),
    Indicador("I2", "Cartera etapa 2 / Cartera bruta", "Cartera etapa 2 ÷ cartera total", "≤ 5 %", lambda c: _etapa(c, 1), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("I3", "Cartera etapa 3 / Cartera bruta", "Cartera etapa 3 ÷ cartera total", "≤ 5 %", lambda c: _etapa(c, 2), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("I4", "Suficiencia de reservas etapa 1 (PCE 12 meses)", "Reserva etapa 1 ÷ PCE etapa 1", "≥ 100 %", lambda c: _suf(c, 0), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("I5", "Suficiencia de reservas etapa 2 (PCE vida del crédito)", "Reserva etapa 2 ÷ PCE etapa 2", "≥ 100 %", lambda c: _suf(c, 1), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("I6", "Suficiencia de reservas etapa 3 (deteriorada)", "Reserva etapa 3 ÷ PCE etapa 3", "≥ 100 %", lambda c: _suf(c, 2), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("I7", "Suficiencia total de reservas (EPRC / PCE)", "EPRC total ÷ PCE total", "≥ 100 %",
              lambda c: (c.pce["suficiencia"], c.pce["reserva_total"], c.pce["pce_total"]) if c.pce["pce_total"] else (None, "Sin pérdida esperada"), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("I8", "Cobertura de cartera etapa 3", "EPRC total ÷ cartera etapa 3", "≥ 100 %", lambda c: _div(c.g("estimaciones"), c.g("cartera_etapa3")), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("I9", "Costo de riesgo", "Estimaciones del ejercicio anualizadas ÷ cartera bruta promedio", "≤ 3 %", lambda c: _flujo(c, "provisiones", "cartera_bruta"), "max", {"SOCAP": (None, 0.03), "SOFOM": (None, 0.03)}),
    Indicador("I10", "Deterioro neto (migración a etapas 2 y 3)", "Δ participación de etapas 2 + 3 vs. periodo anterior", "≤ 0 pp", _i10, "max", {"SOCAP": (None, 0.0), "SOFOM": (None, 0.0)}),
    Indicador("I11", "Capital ajustado por déficit IFRS 9 / Activo total", "(Capital institucional − déficit de reservas vs. PCE) ÷ activo total", "≥ 10 %", _i11, "min", {"SOCAP": (0.10, None), "SOFOM": (0.10, None)}),
    # ------------------------------------------------------------------ K
    Indicador("K1", "Apalancamiento (Pasivo total / Capital contable)", "Pasivo total ÷ capital contable", "≤ 5 veces (SOFOM)", lambda c: _div(c.a["pasivo_total"], c.a["capital_contable"]), "max", {"SOFOM": (None, 5.0)}, formato="veces", aplica=("SOFOM",)),
    Indicador("K2", "Eficiencia operativa (Gastos de administración / Margen bruto)", "Gastos de administración ÷ margen financiero", "≤ 75 %", lambda c: _div(c.g("gastos_administracion"), c.a["margen_bruto"]), "max", {"SOCAP": (None, 0.75), "SOFOM": (None, 0.75)}),
]

INDICADORES_POR_CODIGO = {i.codigo: i for i in INDICADORES}


# ------------------------------------------------------------------ contexto
def _fusion(estado: EstadoFinanciero) -> dict[str, float]:
    d = estado.datos()
    a = agregados(d)
    capital_neto = a["capital_institucional"] + d.get("estimaciones", 0) - d.get("mora_mas_12", 0) - 0.35 * d.get("mora_1_12", 0) - d.get("activos_problematicos", 0)
    return {**d, **a, "capital_neto": capital_neto}


def _meses_entre(a: date, b: date) -> float:
    meses = (b.year - a.year) * 12 + (b.month - a.month)
    if a.day >= 28 and b.day >= 28:  # cortes de fin de mes
        return float(meses)
    return meses + (b.day - a.day) / 30.0


def construir_contexto(db: Session, estado: EstadoFinanciero) -> Contexto:
    entidad = estado.entidad
    previos = [e for e in entidad.estados if e.fecha_corte < estado.fecha_corte]
    cierre_anterior = date(estado.fecha_corte.year - 1, 12, 31)
    puntos = [e for e in previos if e.fecha_corte >= cierre_anterior] + [estado]
    fusiones = [_fusion(e) for e in puntos]
    claves = set().union(*fusiones)
    promedio = {k: sum(f.get(k, 0.0) for f in fusiones) / len(fusiones) for k in claves}

    base, meses_crec = None, None
    candidato = next((e for e in reversed(previos) if e.fecha_corte <= cierre_anterior), None)
    if candidato is None and previos:
        candidato = previos[0]
    if candidato is not None:
        meses_crec = _meses_entre(candidato.fecha_corte, estado.fecha_corte)
        if meses_crec > 0.5:
            base = _fusion(candidato)
        else:
            meses_crec = None
    anterior = _fusion(previos[-1]) if previos else None

    d = estado.datos()
    actual = _fusion(estado)
    meses = estado.fecha_corte.month if estado.fecha_corte.month else 12
    return Contexto(
        entidad=entidad,
        estado=estado,
        d=d,
        a=actual,
        p=promedio,
        factor=12 / meses,
        base=base,
        meses_crec=meses_crec,
        anterior=anterior,
        pce=calcular_pce(d, entidad.params_ifrs9()),
    )


# ------------------------------------------------------------------ evaluación
def _metas_personalizadas(db: Session, tipo: str) -> dict[str, tuple]:
    return {m.codigo: (m.minimo, m.maximo) for m in db.query(MetaIndicador).filter(MetaIndicador.tipo_entidad == tipo).all()}


def _estatus(valor: float, minimo, maximo) -> str:
    def margen(limite):
        return max(abs(limite) * TOLERANCIA, 0.0025)

    if minimo is not None and valor < minimo:
        return "alerta" if valor >= minimo - margen(minimo) else "deficiente"
    if maximo is not None and valor > maximo:
        return "alerta" if valor <= maximo + margen(maximo) else "deficiente"
    return "cumple"


def _brecha(valor, num, den, minimo, maximo):
    """Ajuste requerido en el numerador para alcanzar la meta (en pesos)."""
    if num is None or den is None or not isinstance(num, (int, float)):
        return None
    if minimo is not None and valor < minimo:
        return minimo * den - num
    if maximo is not None and valor > maximo:
        return maximo * den - num
    return None


def calcular_indicadores(db: Session, estado: EstadoFinanciero) -> dict:
    ctx = construir_contexto(db, estado)
    tipo = ctx.entidad.tipo
    personalizadas = _metas_personalizadas(db, tipo)
    filas = []
    # Se evalúan en dos pasadas para resolver metas que dependen de otros indicadores.
    for ind in INDICADORES:
        r = ind.calc(ctx)
        ctx.valores[ind.codigo] = r[0] if len(r) == 3 else None
    for ind in INDICADORES:
        fila = {"ind": ind, "codigo": ind.codigo, "valor": None, "estatus": "na", "nota": "", "minimo": None, "maximo": None, "brecha": None, "numerador": None, "denominador": None}
        if tipo not in ind.aplica:
            fila["nota"] = f"No aplica a {tipo}"
            filas.append(fila)
            continue
        r = ind.calc(ctx)
        if len(r) != 3 or r[0] is None:
            fila["nota"] = r[1] if len(r) == 2 else ""
            filas.append(fila)
            continue
        valor, num, den = r
        fila.update(valor=valor, numerador=num, denominador=den)
        if ind.tipo == "info":
            fila["estatus"] = "informativo"
        elif ind.tipo == "sino":
            fila["estatus"] = "cumple" if valor >= 1 else "deficiente"
        elif ind.tipo == "custom":
            fila["estatus"] = ind.custom(ctx, valor)
        else:
            if ind.limites_dinamicos:
                minimo, maximo = ind.limites_dinamicos(ctx)
            else:
                minimo, maximo = ind.limites.get(tipo, (None, None))
            if ind.codigo in personalizadas:
                minimo, maximo = personalizadas[ind.codigo]
            fila.update(minimo=minimo, maximo=maximo)
            if minimo is None and maximo is None:
                fila["estatus"] = "informativo"
                if ind.limites_dinamicos:
                    fila["nota"] = "Sin meta de referencia: capture inflación y tasas del periodo"
            else:
                fila["estatus"] = _estatus(valor, minimo, maximo)
                if fila["estatus"] != "cumple":
                    fila["brecha"] = _brecha(valor, num, den, minimo, maximo)
        filas.append(fila)

    evaluados = [f for f in filas if f["estatus"] in ("cumple", "alerta", "deficiente")]
    deficientes = [f for f in filas if f["estatus"] == "deficiente"]
    alertas = [f for f in filas if f["estatus"] == "alerta"]
    return {
        "contexto": ctx,
        "filas": filas,
        "por_codigo": {f["codigo"]: f for f in filas},
        "evaluados": len(evaluados),
        "deficientes": deficientes,
        "alertas": alertas,
        "cumplen": len(evaluados) - len(deficientes) - len(alertas),
        "pct_deficientes": len(deficientes) / len(evaluados) if evaluados else 0.0,
        "agregados": ctx.a,
        "pce": ctx.pce,
        "factor": ctx.factor,
    }
