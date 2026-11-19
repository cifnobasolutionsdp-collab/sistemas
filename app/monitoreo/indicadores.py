"""Modelo S-O-L-I-D-E-Z del Sistema de Evaluación y Monitoreo Financiero.

Siete dimensiones: **S**alvaguarda de cartera, **O**rden del balance,
**L**iquidez, **I**ngresos-costos-rentabilidad, **D**eterioro y pérdida
esperada (IFRS 9), **E**ficiencia de activos y **Z**ona de crecimiento.
Además calcula el **Índice SOLIDEZ** (0-100) por dimensión y global.

Los valores se expresan como fracción decimal (0.10 = 10 %), salvo los
indicadores en "veces". Los indicadores de ingresos y costos (I) se
anualizan con base en los meses transcurridos del ejercicio y se dividen
entre el saldo promedio; los de la zona de crecimiento (Z) son crecimientos
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

# Modelo S-O-L-I-D-E-Z: siete dimensiones de la solidez financiera.
GRUPOS = {
    "S": "Salvaguarda de cartera",
    "O": "Orden del balance",
    "L": "Liquidez",
    "I": "Ingresos, costos y rentabilidad",
    "D": "Deterioro y pérdida esperada (IFRS 9)",
    "E": "Eficiencia de activos",
    "Z": "Zona de crecimiento",
}
ORDEN_GRUPOS = "SOLIDEZ"

# Ponderación de cada dimensión en el Índice SOLIDEZ (suma 100).
PESOS_DIMENSION = {"S": 20, "O": 15, "L": 15, "I": 15, "D": 20, "E": 10, "Z": 5}
CALIFICACIONES = [(85, "Sólida", "cumple"), (70, "Estable", "cumple"), (50, "En vigilancia", "alerta"), (0, "Crítica", "deficiente")]


def calificacion(puntaje: float | None) -> tuple[str, str]:
    if puntaje is None:
        return ("Sin evaluar", "na")
    for minimo, nombre, clase in CALIFICACIONES:
        if puntaje >= minimo:
            return (nombre, clase)
    return ("Crítica", "deficiente")


def indice_solidez(filas: list[dict]) -> dict:
    """Puntaje 0-100: cumple = 1, alerta = 0.5, deficiente = 0, por dimensión y ponderado."""
    dimensiones = []
    suma, pesos = 0.0, 0.0
    for g in ORDEN_GRUPOS:
        ev = [f for f in filas if f["ind"].grupo == g and f["estatus"] in ("cumple", "alerta", "deficiente")]
        cuenta = {e: sum(1 for f in ev if f["estatus"] == e) for e in ("cumple", "alerta", "deficiente")}
        puntaje = 100 * (cuenta["cumple"] + 0.5 * cuenta["alerta"]) / len(ev) if ev else None
        if puntaje is not None:
            suma += puntaje * PESOS_DIMENSION[g]
            pesos += PESOS_DIMENSION[g]
        nombre, clase = calificacion(puntaje)
        dimensiones.append({"grupo": g, "nombre": GRUPOS[g], "peso": PESOS_DIMENSION[g], "puntaje": puntaje,
                            "evaluados": len(ev), **cuenta, "calificacion": nombre, "clase": clase})
    global_ = suma / pesos if pesos else None
    nombre, clase = calificacion(global_)
    return {"puntaje": global_, "calificacion": nombre, "clase": clase, "dimensiones": dimensiones}

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


def _s1(ctx):
    if m := _requiere(ctx, "mora_mas_12"):
        return (None, m)
    m12 = ctx.g("mora_mas_12")
    if m12 <= 0:
        return (None, "Sin morosidad mayor a 12 meses")
    return (min(ctx.g("estimaciones"), m12) / m12, min(ctx.g("estimaciones"), m12), m12)


def _s2(ctx):
    if m := _requiere(ctx, "mora_1_12", "mora_mas_12"):
        return (None, m)
    m112 = ctx.g("mora_1_12")
    netas = ctx.g("estimaciones") - min(ctx.g("estimaciones"), ctx.g("mora_mas_12"))
    return _div(netas, m112) if m112 > 0 else (None, "Sin morosidad de 1 a 12 meses")


def _s3(ctx):
    if m := _requiere(ctx, "mora_mas_12"):
        return (None, m)
    return (1.0 if ctx.g("mora_mas_12") <= 0 else 0.0, None, None)


def _s6(ctx):
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


def _i12_custom(ctx, valor):
    if valor <= 0:
        return "deficiente"
    e8, s8, s11 = ctx.valores.get("O8"), ctx.valores.get("Z8"), ctx.valores.get("Z11")
    if e8 is not None and e8 < 0.10 and s8 is not None and s11 is not None and s8 < s11:
        return "alerta"
    return "cumple"


def _i10_custom(ctx, valor):
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


def _d10(ctx):
    if not ctx.anterior:
        return (None, "Requiere un periodo anterior cargado")
    def pct(x):
        tot = x.get("cartera_etapa1", 0) + x.get("cartera_etapa2", 0) + x.get("cartera_etapa3", 0)
        return (x.get("cartera_etapa2", 0) + x.get("cartera_etapa3", 0)) / tot if tot else None
    act, ant = pct({**ctx.d}), pct(ctx.anterior)
    if act is None or ant is None:
        return (None, "Sin cartera por etapas")
    return (act - ant, None, None)


def _d11(ctx):
    return _div(_capital_e8(ctx) - ctx.pce["deficit"], ctx.a["activo_total"])


SOCAP = ("SOCAP",)

INDICADORES: list[Indicador] = [
    # ------------------------------------------------------------------ S · Salvaguarda de cartera
    Indicador("S1", "Cobertura de mora mayor a 12 meses", "min(EPRC, mora>12) ÷ mora>12", "100 %", _s1, "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("S2", "Cobertura de mora de 1 a 12 meses", "(EPRC − cobertura de mora>12) ÷ mora 1-12", "≥ 35 %", _s2, "min", {"SOCAP": (0.35, None), "SOFOM": (0.35, None)}),
    Indicador("S3", "Saneamiento total de cartera mayor a 12 meses", "¿Cartera morosa > 12 meses = 0?", "Sí", _s3, "sino", formato="sino"),
    Indicador("S4", "Intensidad de castigos", "Castigos del ejercicio anualizados ÷ cartera bruta promedio", "Lo mínimo",
              lambda c: _div(c.g("castigos_ejercicio") * c.factor, c.prom("cartera_bruta")) if c.tiene("castigos_ejercicio") else (None, "Requiere dato complementario: castigos_ejercicio"), "info"),
    Indicador("S5", "Efectividad en la recuperación de castigos", "Recuperaciones acumuladas ÷ castigos acumulados", "> 75 %",
              lambda c: _div(c.g("recuperaciones_acumuladas"), c.g("castigos_acumulados")) if c.g("castigos_acumulados") else (None, "Sin castigos acumulados"), "min", {"SOCAP": (0.75, None), "SOFOM": (0.75, None)}),
    Indicador("S6", "Respaldo patrimonial al ahorrador (solvencia)", "(Activo + EPRC − mora>12 − 35 % mora 1-12 − pasivo − activos problemáticos + depósitos) ÷ (depósitos + aportaciones)", "≥ 111 %", _s6, "min", {"SOCAP": (1.11, None)}, aplica=SOCAP),
    # ------------------------------------------------------------------ O · Orden del balance
    Indicador("O1", "Colocación productiva del activo", "Cartera neta ÷ activo total", "70 % – 80 %", lambda c: _div(c.a["cartera_neta"], c.a["activo_total"]), "rango", {"SOCAP": (0.70, 0.80), "SOFOM": (0.70, 0.95)}),
    Indicador("O2", "Peso de la liquidez en el activo", "(Disponibilidades + inversiones CP) ÷ activo total", "≤ 16 %", lambda c: _div(c.a["inversiones_liquidas"], c.a["activo_total"]), "max", {"SOCAP": (None, 0.16), "SOFOM": (None, 0.16)}),
    Indicador("O3", "Peso de las inversiones financieras", "Inversiones LP ÷ activo total", "≤ 2 %", lambda c: _div(c.g("inversiones_lp"), c.a["activo_total"]), "max", {"SOCAP": (None, 0.02), "SOFOM": (None, 0.02)}),
    Indicador("O4", "Inmovilización en inversiones no financieras", "Inversiones permanentes ÷ activo total", "0 %", lambda c: _div(c.g("inversiones_permanentes"), c.a["activo_total"]), "max", {"SOCAP": (None, 0.0), "SOFOM": (None, 0.0)}),
    Indicador("O5", "Fondeo con ahorro de socios", "Depósitos ÷ activo total", "70 % – 80 %", lambda c: _div(c.a["depositos"], c.a["activo_total"]), "rango", {"SOCAP": (0.70, 0.80)}, aplica=SOCAP),
    Indicador("O6", "Dependencia de fondeo externo", "Préstamos bancarios ÷ activo total", "0 % – 5 %", lambda c: _div(c.g("prestamos_bancarios"), c.a["activo_total"]), "rango", {"SOCAP": (0.0, 0.05), "SOFOM": (None, None)}),
    Indicador("O7", "Peso de las aportaciones de socios", "Capital social ÷ activo total", "10 % – 20 %", lambda c: _div(c.g("capital_social"), c.a["activo_total"]), "rango", {"SOCAP": (0.10, 0.20)}, aplica=SOCAP),
    Indicador("O8", "Fortaleza patrimonial", "Reservas + resultados ÷ activo total (SOFOM: capital contable)", "≥ 10 %", lambda c: _div(_capital_e8(c), c.a["activo_total"]), "min", {"SOCAP": (0.10, None), "SOFOM": (0.10, None)}),
    Indicador("O9", "Fortaleza patrimonial neta de riesgos", "(Capital institucional + EPRC − mora>12 − 35 % mora 1-12 − activos problemáticos) ÷ activo", "≥ 10 %", lambda c: _div(_capital_neto(c), c.a["activo_total"]), "min", {"SOCAP": (0.10, None), "SOFOM": (0.10, None)}),
    Indicador("O10", "Apalancamiento (pasivo / capital contable)", "Pasivo total ÷ capital contable", "≤ 5 veces (SOFOM)", lambda c: _div(c.a["pasivo_total"], c.a["capital_contable"]), "max", {"SOFOM": (None, 5.0)}, formato="veces", aplica=("SOFOM",)),
    # ------------------------------------------------------------------ L · Liquidez
    Indicador("L1", "Liquidez disponible para ahorradores", "(Inversiones líquidas − CxP ≤ 30 días) ÷ depósitos", "≥ 15 %", lambda c: _div(c.a["inversiones_liquidas"] - c.g("cxp_30_dias"), c.a["depositos"]), "min", {"SOCAP": (0.15, None)}, aplica=SOCAP),
    Indicador("L2", "Reserva de liquidez", "Reserva de liquidez ÷ depósitos", "≥ 10 %", lambda c: _div(c.g("reserva_liquidez"), c.a["depositos"]) if c.tiene("reserva_liquidez") else (None, "Requiere dato complementario: reserva_liquidez"), "min", {"SOCAP": (0.10, None)}, aplica=SOCAP),
    Indicador("L3", "Efectivo ocioso", "Caja sin rendimiento ÷ activo total", "< 1 %", lambda c: _div(c.g("caja"), c.a["activo_total"]), "max", {"SOCAP": (None, 0.01), "SOFOM": (None, 0.01)}),
    # ------------------------------------------------------------------ I · Ingresos, costos y rentabilidad
    Indicador("I1", "Rendimiento de la cartera de crédito", "Intereses de cartera anualizados ÷ cartera neta promedio", "≥ Tasa empresarial", lambda c: _flujo(c, "ing_intereses_cartera", "cartera_neta"), "min",
              limites_dinamicos=lambda c: (c.estado.tasa_empresarial, None)),
    Indicador("I2", "Rendimiento de la liquidez", "Ingresos de disponibilidades anualizados ÷ inversiones líquidas promedio", "≥ Tasa de mercado", lambda c: _flujo(c, "ing_disponibilidades", "inversiones_liquidas"), "min",
              limites_dinamicos=lambda c: (c.estado.tasa_mercado, None)),
    Indicador("I3", "Rendimiento de inversiones financieras", "Ingresos de inversiones LP anualizados ÷ inversiones LP promedio", "≥ Tasa de mercado", lambda c: _flujo(c, "ing_inversiones_lp", "inversiones_lp"), "min",
              limites_dinamicos=lambda c: (c.estado.tasa_mercado, None)),
    Indicador("I4", "Rendimiento de inversiones no financieras", "Ingresos de inv. permanentes anualizados ÷ promedio", "≥ I1", lambda c: _flujo(c, "ing_inversiones_permanentes", "inversiones_permanentes"), "min",
              limites_dinamicos=lambda c: (c.valores.get("I1"), None)),
    Indicador("I5", "Costo del ahorro", "Intereses de depósitos anualizados ÷ depósitos promedio", "≥ Inflación (tasa real positiva)", lambda c: _flujo(c, "int_depositos", "depositos"), "min",
              limites_dinamicos=lambda c: (c.inflacion, None), aplica=SOCAP),
    Indicador("I6", "Costo del fondeo externo", "Intereses de préstamos bancarios anualizados ÷ promedio", "≥ I5 (SOFOM: ≤ I1)", lambda c: _flujo(c, "int_prestamos_bancarios", "prestamos_bancarios"), "rango",
              limites_dinamicos=lambda c: (None, c.valores.get("I1")) if c.entidad.tipo == "SOFOM" else (c.valores.get("I5"), None)),
    Indicador("I7", "Costo de las aportaciones", "Rendimientos de aportaciones anualizados ÷ capital social promedio", "≤ I5", lambda c: _flujo(c, "int_aportaciones", "capital_social"), "max",
              limites_dinamicos=lambda c: (None, c.valores.get("I5")), aplica=SOCAP),
    Indicador("I8", "Margen financiero sobre activos", "Margen financiero anualizado ÷ activo promedio", "≥ I9 + I10", lambda c: _flujo(c, "margen_bruto", "activo_total"), "min",
              limites_dinamicos=lambda c: ((c.valores.get("I9") or 0) + (c.valores.get("I10") or 0), None)),
    Indicador("I9", "Carga operativa sobre activos", "Gastos de administración anualizados ÷ activo promedio", "3 % – 10 %", lambda c: _flujo(c, "gastos_administracion", "activo_total"), "rango", {"SOCAP": (0.03, 0.10), "SOFOM": (0.03, 0.10)}),
    Indicador("I10", "Carga de estimaciones sobre activos", "Estimaciones del ejercicio anualizadas ÷ activo promedio", "Suficiente para cubrir la PCE (IFRS 9)", lambda c: _flujo(c, "provisiones", "activo_total"), "custom", custom=_i10_custom),
    Indicador("I11", "Resultados no recurrentes sobre activos", "(Otros ingresos − otros gastos) anualizados ÷ activo promedio", "Lo mínimo", lambda c: _flujo(c, "otros_neto", "activo_total"), "info"),
    Indicador("I12", "Rentabilidad sobre activos (ROA)", "Resultado neto anualizado ÷ activo promedio", "> 0 y suficiente para alcanzar O8", lambda c: _flujo(c, "excedente_neto", "activo_total"), "custom", custom=_i12_custom),
    Indicador("I13", "Rentabilidad sobre capital institucional (ROC)", "Resultado neto anualizado ÷ capital institucional promedio", "> Inflación", lambda c: _flujo(c, "excedente_neto", "capital_institucional"), "min",
              limites_dinamicos=lambda c: (c.inflacion, None)),
    Indicador("I14", "Eficiencia operativa (gastos / margen financiero)", "Gastos de administración ÷ margen financiero", "≤ 75 %", lambda c: _div(c.g("gastos_administracion"), c.a["margen_bruto"]), "max", {"SOCAP": (None, 0.75), "SOFOM": (None, 0.75)}),
    # ------------------------------------------------------------------ D · Deterioro y pérdida esperada (IFRS 9)
    Indicador("D1", "Cartera sana (etapa 1)", "Cartera etapa 1 ÷ cartera total", "≥ 90 %", lambda c: _etapa(c, 0), "min", {"SOCAP": (0.90, None), "SOFOM": (0.90, None)}),
    Indicador("D2", "Cartera en vigilancia (etapa 2)", "Cartera etapa 2 ÷ cartera total", "≤ 5 %", lambda c: _etapa(c, 1), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("D3", "Cartera deteriorada (etapa 3)", "Cartera etapa 3 ÷ cartera total", "≤ 5 %", lambda c: _etapa(c, 2), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("D4", "Suficiencia de reservas — etapa 1 (PCE 12 meses)", "Reserva etapa 1 ÷ PCE etapa 1", "≥ 100 %", lambda c: _suf(c, 0), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("D5", "Suficiencia de reservas — etapa 2 (PCE vida del crédito)", "Reserva etapa 2 ÷ PCE etapa 2", "≥ 100 %", lambda c: _suf(c, 1), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("D6", "Suficiencia de reservas — etapa 3", "Reserva etapa 3 ÷ PCE etapa 3", "≥ 100 %", lambda c: _suf(c, 2), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("D7", "Suficiencia total de reservas vs. pérdida esperada", "EPRC total ÷ PCE total", "≥ 100 %",
              lambda c: (c.pce["suficiencia"], c.pce["reserva_total"], c.pce["pce_total"]) if c.pce["pce_total"] else (None, "Sin pérdida esperada"), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("D8", "Cobertura de cartera deteriorada", "EPRC total ÷ cartera etapa 3", "≥ 100 %", lambda c: _div(c.g("estimaciones"), c.g("cartera_etapa3")), "min", {"SOCAP": (1.0, None), "SOFOM": (1.0, None)}),
    Indicador("D9", "Costo de riesgo", "Estimaciones del ejercicio anualizadas ÷ cartera bruta promedio", "≤ 3 %", lambda c: _flujo(c, "provisiones", "cartera_bruta"), "max", {"SOCAP": (None, 0.03), "SOFOM": (None, 0.03)}),
    Indicador("D10", "Migración neta a etapas 2 y 3", "Δ participación de etapas 2 + 3 vs. periodo anterior", "≤ 0 pp", _d10, "max", {"SOCAP": (None, 0.0), "SOFOM": (None, 0.0)}),
    Indicador("D11", "Capital ajustado por pérdida esperada", "(Capital institucional − déficit de reservas vs. PCE) ÷ activo total", "≥ 10 %", _d11, "min", {"SOCAP": (0.10, None), "SOFOM": (0.10, None)}),
    # ------------------------------------------------------------------ E · Eficiencia de activos
    Indicador("E1", "Índice de morosidad", "Cartera morosa (o etapa 3) ÷ cartera bruta", "≤ 5 %", lambda c: _div(c.a["morosidad_total"], c.a["cartera_bruta"]), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("E2", "Activos que no generan ingresos", "(Caja + CxC + adjudicados + activo fijo + otros) ÷ activo total", "≤ 5 %", lambda c: _div(c.a["activo_improductivo"], c.a["activo_total"]), "max", {"SOCAP": (None, 0.05), "SOFOM": (None, 0.05)}),
    Indicador("E3", "Financiamiento sin costo del activo improductivo", "(Capital institucional + pasivos sin costo) ÷ activo improductivo", "≥ 200 %", lambda c: _div(c.a["capital_institucional"] + c.a["pasivo_sin_costo"], c.a["activo_improductivo"]), "min", {"SOCAP": (2.0, None), "SOFOM": (2.0, None)}),
    # ------------------------------------------------------------------ Z · Zona de crecimiento
    Indicador("Z1", "Crecimiento de la cartera neta", "Crecimiento anualizado", "≥ Inflación (para alcanzar O1)", lambda c: _crec(c, "cartera_neta"), "min", limites_dinamicos=lambda c: (c.inflacion, None)),
    Indicador("Z2", "Crecimiento de la liquidez", "Crecimiento anualizado", "Congruente con O2", lambda c: _crec(c, "inversiones_liquidas"), "info"),
    Indicador("Z3", "Crecimiento de inversiones financieras", "Crecimiento anualizado", "Congruente con O3", lambda c: _crec(c, "inversiones_lp"), "info"),
    Indicador("Z4", "Crecimiento de inversiones no financieras", "Crecimiento anualizado", "Congruente con O4", lambda c: _crec(c, "inversiones_permanentes"), "info"),
    Indicador("Z5", "Crecimiento del ahorro", "Crecimiento anualizado", "≥ Inflación (para alcanzar O5)", lambda c: _crec(c, "depositos"), "min", limites_dinamicos=lambda c: (c.inflacion, None), aplica=SOCAP),
    Indicador("Z6", "Crecimiento del fondeo externo", "Crecimiento anualizado", "Congruente con O6", lambda c: _crec(c, "prestamos_bancarios"), "info"),
    Indicador("Z7", "Crecimiento de aportaciones", "Crecimiento anualizado", "≥ Inflación (para alcanzar O7)", lambda c: _crec(c, "capital_social"), "min", limites_dinamicos=lambda c: (c.inflacion, None), aplica=SOCAP),
    Indicador("Z8", "Crecimiento del capital institucional", "Crecimiento anualizado", "≥ crecimiento del activo (Z11)", lambda c: _crec(c, "capital_institucional"), "min", limites_dinamicos=lambda c: (c.valores.get("Z11"), None)),
    Indicador("Z9", "Crecimiento del capital neto", "Crecimiento anualizado", "Congruente con O9", lambda c: _crec(c, "capital_neto"), "info"),
    Indicador("Z10", "Crecimiento de socios", "Crecimiento anualizado", "≥ Inflación", lambda c: _crec(c, "asociados"), "min", limites_dinamicos=lambda c: (c.inflacion, None)),
    Indicador("Z11", "Crecimiento del activo total", "Crecimiento anualizado", "≥ Inflación", lambda c: _crec(c, "activo_total"), "min", limites_dinamicos=lambda c: (c.inflacion, None)),
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
        "indice": indice_solidez(filas),
        "agregados": ctx.a,
        "pce": ctx.pce,
        "factor": ctx.factor,
    }
