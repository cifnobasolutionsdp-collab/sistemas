"""Rubros financieros estándar del módulo de monitoreo.

Cada estado financiero (o balanza de comprobación) importado se resume en un
diccionario ``{clave_rubro: importe}``. Los indicadores financieros e IFRS 9 se
calculan exclusivamente a partir de estos rubros, lo que permite recibir
información de entidades con catálogos de cuentas distintos.

Convención de signos: todos los importes se expresan en valor positivo según
la naturaleza del rubro (los activos, pasivos, ingresos y gastos son
positivos; las estimaciones se registran en positivo aunque restan al
activo). Sólo el resultado del ejercicio puede ser negativo (pérdida).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rubro:
    clave: str
    concepto: str
    estado: str  # balance | resultados | complementario
    seccion: str
    signo: int = 1  # +1 naturaleza deudora (activo/gasto), -1 acreedora


RUBROS: list[Rubro] = [
    # ----------------------------------------------------------- Balance: activo
    Rubro("caja", "Caja y efectivo sin rendimiento", "balance", "Activo", 1),
    Rubro("bancos", "Bancos y disponibilidades con rendimiento", "balance", "Activo", 1),
    Rubro("inversiones_cp", "Inversiones en valores de corto plazo (≤ 1 año)", "balance", "Activo", 1),
    Rubro("inversiones_lp", "Inversiones financieras de largo plazo (> 1 año)", "balance", "Activo", 1),
    Rubro("cartera_etapa1", "Cartera de crédito con riesgo etapa 1", "balance", "Activo", 1),
    Rubro("cartera_etapa2", "Cartera de crédito con riesgo etapa 2", "balance", "Activo", 1),
    Rubro("cartera_etapa3", "Cartera de crédito con riesgo etapa 3 (vencida)", "balance", "Activo", 1),
    Rubro("estimaciones", "Estimación preventiva para riesgos crediticios (EPRC)", "balance", "Activo", -1),
    Rubro("cuentas_por_cobrar", "Otras cuentas por cobrar (neto)", "balance", "Activo", 1),
    Rubro("bienes_adjudicados", "Bienes adjudicados (neto)", "balance", "Activo", 1),
    Rubro("activo_fijo", "Propiedades, mobiliario y equipo (neto)", "balance", "Activo", 1),
    Rubro("inversiones_permanentes", "Inversiones permanentes / no financieras", "balance", "Activo", 1),
    Rubro("otros_activos", "Otros activos (cargos diferidos, intangibles)", "balance", "Activo", 1),
    # ----------------------------------------------------------- Balance: pasivo
    Rubro("depositos_vista", "Depósitos de exigibilidad inmediata", "balance", "Pasivo", -1),
    Rubro("depositos_plazo", "Depósitos a plazo", "balance", "Pasivo", -1),
    Rubro("prestamos_bancarios", "Préstamos bancarios y de otros organismos (crédito externo)", "balance", "Pasivo", -1),
    Rubro("cuentas_por_pagar", "Otras cuentas por pagar (sin costo)", "balance", "Pasivo", -1),
    Rubro("otros_pasivos", "Créditos diferidos y otros pasivos (sin costo)", "balance", "Pasivo", -1),
    # ----------------------------------------------------------- Balance: capital
    Rubro("capital_social", "Capital social / certificados de aportación", "balance", "Capital", -1),
    Rubro("reservas_capital", "Fondo de reserva y otras reservas de capital", "balance", "Capital", -1),
    Rubro("resultados_anteriores", "Resultado de ejercicios anteriores", "balance", "Capital", -1),
    Rubro("resultado_ejercicio", "Resultado neto del ejercicio", "balance", "Capital", -1),
    # ----------------------------------------------------------- Resultados: ingresos
    Rubro("ing_intereses_cartera", "Ingresos por intereses de cartera de crédito", "resultados", "Ingresos", -1),
    Rubro("ing_disponibilidades", "Ingresos por disponibilidades e inversiones de corto plazo", "resultados", "Ingresos", -1),
    Rubro("ing_inversiones_lp", "Ingresos por inversiones financieras de largo plazo", "resultados", "Ingresos", -1),
    Rubro("ing_inversiones_permanentes", "Ingresos por inversiones no financieras / permanentes", "resultados", "Ingresos", -1),
    Rubro("comisiones_cobradas", "Comisiones y tarifas cobradas", "resultados", "Ingresos", -1),
    Rubro("otros_ingresos", "Otros ingresos de la operación", "resultados", "Ingresos", -1),
    # ----------------------------------------------------------- Resultados: gastos
    Rubro("int_depositos", "Gastos por intereses de depósitos", "resultados", "Gastos", 1),
    Rubro("int_prestamos_bancarios", "Gastos por intereses de préstamos bancarios", "resultados", "Gastos", 1),
    Rubro("int_aportaciones", "Rendimientos pagados sobre aportaciones", "resultados", "Gastos", 1),
    Rubro("comisiones_pagadas", "Comisiones y tarifas pagadas", "resultados", "Gastos", 1),
    Rubro("provisiones", "Estimación preventiva para riesgos crediticios (cargo a resultados)", "resultados", "Gastos", 1),
    Rubro("gastos_administracion", "Gastos de administración y promoción", "resultados", "Gastos", 1),
    Rubro("otros_gastos", "Otros gastos de la operación", "resultados", "Gastos", 1),
    Rubro("impuestos", "Impuestos y PTU", "resultados", "Gastos", 1),
    # ----------------------------------------------------------- Datos complementarios
    Rubro("mora_1_12", "Cartera morosa de 1 a 12 meses", "complementario", "Cartera", 1),
    Rubro("mora_mas_12", "Cartera morosa mayor a 12 meses", "complementario", "Cartera", 1),
    Rubro("castigos_ejercicio", "Castigos / depuraciones de cartera del ejercicio", "complementario", "Cartera", 1),
    Rubro("castigos_acumulados", "Castigos / depuraciones acumuladas (histórico)", "complementario", "Cartera", 1),
    Rubro("recuperaciones_acumuladas", "Recuperaciones acumuladas de cartera castigada", "complementario", "Cartera", 1),
    Rubro("reserva_etapa1", "Estimación constituida etapa 1", "complementario", "IFRS 9", 1),
    Rubro("reserva_etapa2", "Estimación constituida etapa 2", "complementario", "IFRS 9", 1),
    Rubro("reserva_etapa3", "Estimación constituida etapa 3", "complementario", "IFRS 9", 1),
    Rubro("pe_etapa1", "Pérdida crediticia esperada calculada por la entidad — etapa 1", "complementario", "IFRS 9", 1),
    Rubro("pe_etapa2", "Pérdida crediticia esperada calculada por la entidad — etapa 2", "complementario", "IFRS 9", 1),
    Rubro("pe_etapa3", "Pérdida crediticia esperada calculada por la entidad — etapa 3", "complementario", "IFRS 9", 1),
    Rubro("activos_problematicos", "Activos problemáticos / pérdidas por liquidar", "complementario", "Otros", 1),
    Rubro("cxp_30_dias", "Cuentas por pagar a corto plazo (≤ 30 días)", "complementario", "Liquidez", 1),
    Rubro("reserva_liquidez", "Reserva de liquidez / encaje (en entidad de segundo piso)", "complementario", "Liquidez", 1),
    Rubro("asociados", "Número de socios / asociados (o acreditados)", "complementario", "Otros", 1),
]

RUBROS_POR_CLAVE = {r.clave: r for r in RUBROS}

ESTADOS = {
    "balance": "Balance General",
    "resultados": "Estado de Resultados",
    "complementario": "Datos complementarios",
}


def rubros_de(estado: str) -> list[Rubro]:
    return [r for r in RUBROS if r.estado == estado]


def agregados(r: dict[str, float]) -> dict[str, float]:
    """Calcula los agregados que utilizan los indicadores."""
    g = lambda k: float(r.get(k) or 0.0)  # noqa: E731
    a: dict[str, float] = {}
    a["cartera_bruta"] = g("cartera_etapa1") + g("cartera_etapa2") + g("cartera_etapa3")
    a["cartera_neta"] = a["cartera_bruta"] - g("estimaciones")
    a["disponibilidades"] = g("caja") + g("bancos")
    a["inversiones_liquidas"] = a["disponibilidades"] + g("inversiones_cp")
    a["activo_improductivo"] = (
        g("caja") + g("cuentas_por_cobrar") + g("bienes_adjudicados") + g("activo_fijo") + g("otros_activos")
    )
    a["activo_total"] = (
        a["inversiones_liquidas"] + g("inversiones_lp") + a["cartera_neta"] + g("cuentas_por_cobrar")
        + g("bienes_adjudicados") + g("activo_fijo") + g("inversiones_permanentes") + g("otros_activos")
    )
    a["depositos"] = g("depositos_vista") + g("depositos_plazo")
    a["pasivo_sin_costo"] = g("cuentas_por_pagar") + g("otros_pasivos")
    a["pasivo_total"] = a["depositos"] + g("prestamos_bancarios") + a["pasivo_sin_costo"]
    a["capital_institucional"] = g("reservas_capital") + g("resultados_anteriores") + g("resultado_ejercicio")
    a["capital_contable"] = g("capital_social") + a["capital_institucional"]
    ingresos = sum(g(x.clave) for x in rubros_de("resultados") if x.seccion == "Ingresos")
    gastos = sum(g(x.clave) for x in rubros_de("resultados") if x.seccion == "Gastos")
    a["ingresos_totales"] = ingresos
    a["gastos_totales"] = gastos
    a["costos_financieros"] = g("int_depositos") + g("int_prestamos_bancarios") + g("int_aportaciones")
    a["ingresos_financieros"] = (
        g("ing_intereses_cartera") + g("ing_disponibilidades") + g("ing_inversiones_lp")
        + g("ing_inversiones_permanentes") + g("comisiones_cobradas")
    )
    a["margen_bruto"] = a["ingresos_financieros"] - a["costos_financieros"] - g("comisiones_pagadas")
    a["otros_neto"] = g("otros_ingresos") - g("otros_gastos")
    a["excedente_neto"] = ingresos - gastos
    # Morosidad: se prefiere el dato por antigüedad; si no existe, etapa 3.
    mora = g("mora_1_12") + g("mora_mas_12")
    a["morosidad_total"] = mora if mora > 0 else g("cartera_etapa3")
    a["descuadre"] = a["activo_total"] - a["pasivo_total"] - a["capital_contable"]
    return a
