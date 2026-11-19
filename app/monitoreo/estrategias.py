"""Estrategias de mejora, interrelación de indicadores y plan de acción.

Las estrategias e interrelaciones de los indicadores PERLAS provienen del
archivo "Perlitas" (metodología PERLAS del Consejo Mundial de Cooperativas de
Ahorro y Crédito, WOCCU). Se complementan con estrategias para los
indicadores IFRS 9 (pérdida crediticia esperada) y de solvencia/eficiencia.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ESTRATEGIAS_ADICIONALES: dict[str, list[str]] = {
    "S2": ["Seguir las estrategias mencionadas en E2, Inversiones líquidas: canalizar los excedentes de liquidez a cartera de crédito sana conforme al plan de tesorería."],
    "S3": ["Seguir las estrategias mencionadas en E3, Inversiones financieras, privilegiando instrumentos seguros y de plazo congruente con el calce de pasivos."],
    "S4": ["Seguir las estrategias mencionadas en E4, Inversiones no financieras: no incrementar activos que no generen rendimiento financiero."],
    "S9": ["Seguir las estrategias mencionadas en E9, Capital institucional neto: capitalizar excedentes y cubrir al 100 % la cartera en riesgo con estimaciones."],
    "R11": ["Reducir partidas extraordinarias; documentar y analizar mensualmente los otros ingresos y gastos para que no distorsionen el excedente operativo."],
    "R13": ["Mejorar el ROA (R12) mediante margen bruto suficiente (R8) y control de gastos (R9).", "Capitalizar a la reserva los excedentes para que el capital institucional crezca en términos reales."],
    "I1": [
        "Fortalecer la originación: análisis de capacidad de pago, historial en sociedades de información crediticia y scoring por producto.",
        "Monitorear alertas tempranas (primer atraso, reestructuras, sobreendeudamiento) para evitar la migración a etapa 2.",
        "Diseñar productos y plazos acordes al flujo del acreditado para mantener la cartera al corriente.",
    ],
    "I2": [
        "Definir y documentar el criterio de incremento significativo del riesgo (p. ej. > 30 días de atraso, reestructura, deterioro en buró) y aplicarlo de forma consistente.",
        "Gestión de cobranza preventiva sobre la cartera de etapa 2 para regresarla a etapa 1 (curas) antes de que llegue a deterioro.",
        "Restringir renovaciones y reestructuras que sólo difieren el reconocimiento del deterioro.",
    ],
    "I3": [
        "Seguir las estrategias de A1 (morosidad): cobranza extrajudicial y judicial oportuna, unidad especializada de recuperación.",
        "Depurar (castigar) la cartera deteriorada totalmente reservada conforme a la política aprobada por el Consejo (P3/P4).",
        "Analizar cosechas (vintage) por producto, sucursal y promotor para corregir originación deficiente.",
    ],
    "I4": [
        "Constituir mensualmente la PCE a 12 meses de la cartera etapa 1 con PD calibradas a la experiencia histórica de la entidad.",
        "Incorporar información prospectiva (escenarios macroeconómicos) en la PD, revisando trimestralmente sus ponderaciones.",
    ],
    "I5": [
        "Reconocer la PCE por toda la vida del crédito para la cartera de etapa 2.",
        "Revisar la LGD por tipo de garantía (líquida, hipotecaria, prendaria, sin garantía) para que la reserva refleje la recuperación esperada.",
    ],
    "I6": [
        "Reservar la cartera etapa 3 al nivel de su pérdida esperada (PD = 100 %), descontando sólo garantías ejecutables y valuadas.",
        "Destinar las recuperaciones de cartera castigada (P5) a fortalecer la estimación.",
    ],
    "I7": [
        "Cubrir el déficit de reservas contra la PCE con cargo a resultados de forma gradual y programada, informando al Consejo y a la autoridad.",
        "Ajustar la tasa activa para incorporar el costo de riesgo (prima por pérdida esperada) en el precio de los créditos (R1).",
        "Priorizar la aplicación del excedente: primero estimaciones, luego capitalización y por último distribución.",
    ],
    "I8": ["Seguir las estrategias de I6 e I7: la EPRC total debe cubrir al menos el 100 % de la cartera deteriorada."],
    "I9": [
        "Reducir el costo de riesgo mejorando la originación (scoring, capacidad de pago) y la cobranza temprana.",
        "Fijar precios ajustados por riesgo: la tasa activa debe cubrir costo de fondeo + gastos operativos + pérdida esperada + margen para capital.",
    ],
    "I10": [
        "Dar seguimiento mensual a la matriz de transición entre etapas (1→2, 2→3 y curas) por producto y sucursal.",
        "Activar planes de cobranza preventiva sobre los segmentos con mayor migración.",
    ],
    "I11": [
        "Capitalizar excedentes y, en su caso, aportaciones adicionales para absorber el déficit de reservas IFRS 9 sin bajar del 10 % de capital/activo.",
        "Elaborar un plan de transición para el reconocimiento del déficit que preserve el nivel de capitalización requerido por la regulación.",
    ],
    "K1": [
        "Reducir el apalancamiento capitalizando utilidades y/o con aportaciones de capital de los accionistas.",
        "Diversificar y escalonar el fondeo (banca de desarrollo, emisiones, líneas revolventes) para evitar concentraciones de vencimientos.",
    ],
    "K2": [
        "Controlar el gasto mediante presupuesto autorizado y seguimiento mensual de desviaciones (R9).",
        "Digitalizar procesos de originación y cobranza para lograr economías de escala.",
        "Incrementar el margen bruto (R8) ajustando tasas activas y pasivas.",
    ],
}

INTERRELACION_ADICIONAL: dict[str, dict[str, list[str]]] = {
    "I1": {"afecta": ["I4", "I7", "A1", "R10"], "afectado_por": ["I2", "I3", "S1"], "afecta_indirecta": ["R12", "E8"], "afectado_por_indirecta": ["R1"]},
    "I2": {"afecta": ["I5", "I7", "R10", "I10"], "afectado_por": ["A1", "S1"], "afecta_indirecta": ["R12", "E8", "I11"], "afectado_por_indirecta": ["R1"]},
    "I3": {"afecta": ["A1", "I6", "I7", "I8", "R10", "P1", "P2"], "afectado_por": ["P3", "P4", "I2"], "afecta_indirecta": ["R12", "E8", "E9", "I11"], "afectado_por_indirecta": ["S1"]},
    "I4": {"afecta": ["I7", "R10"], "afectado_por": ["I1", "R8"], "afecta_indirecta": ["R12"], "afectado_por_indirecta": []},
    "I5": {"afecta": ["I7", "R10"], "afectado_por": ["I2", "R8"], "afecta_indirecta": ["R12"], "afectado_por_indirecta": []},
    "I6": {"afecta": ["I7", "I8", "P1", "P2", "R10"], "afectado_por": ["I3", "P5", "R8"], "afecta_indirecta": ["R12", "E9"], "afectado_por_indirecta": []},
    "I7": {"afecta": ["I11", "R10", "R12", "E9"], "afectado_por": ["I4", "I5", "I6", "R8", "P5"], "afecta_indirecta": ["E8", "S8"], "afectado_por_indirecta": ["A1"]},
    "I8": {"afecta": ["E9", "P6"], "afectado_por": ["I3", "R10"], "afecta_indirecta": ["I11"], "afectado_por_indirecta": []},
    "I9": {"afecta": ["R8", "R12", "R10"], "afectado_por": ["A1", "I2", "I3"], "afecta_indirecta": ["E8", "S8"], "afectado_por_indirecta": ["S1"]},
    "I10": {"afecta": ["I2", "I3", "I9"], "afectado_por": ["S1", "A1"], "afecta_indirecta": ["R12"], "afectado_por_indirecta": []},
    "I11": {"afecta": ["E8", "P6"], "afectado_por": ["I7", "R12"], "afecta_indirecta": ["S8"], "afectado_por_indirecta": []},
    "K1": {"afecta": ["E8", "R6"], "afectado_por": ["E6", "S6", "R12"], "afecta_indirecta": ["R12"], "afectado_por_indirecta": []},
    "K2": {"afecta": ["R12", "E8"], "afectado_por": ["R8", "R9"], "afecta_indirecta": ["S8"], "afectado_por_indirecta": []},
    "S2": {"afecta": ["E2", "S11"], "afectado_por": ["S5", "S1"], "afecta_indirecta": ["R8"], "afectado_por_indirecta": []},
    "S3": {"afecta": ["E3", "S11"], "afectado_por": ["S5"], "afecta_indirecta": ["R8"], "afectado_por_indirecta": []},
    "S4": {"afecta": ["E4", "A2"], "afectado_por": ["S8"], "afecta_indirecta": ["R8"], "afectado_por_indirecta": []},
    "S9": {"afecta": ["E9"], "afectado_por": ["S8", "P1", "P2"], "afecta_indirecta": [], "afectado_por_indirecta": []},
    "P6": {"afecta": ["E9", "S5"], "afectado_por": ["P1", "P2", "A1", "E8"], "afecta_indirecta": ["S7"], "afectado_por_indirecta": ["R12"]},
    "E9": {"afecta": ["P6", "S9"], "afectado_por": ["E8", "P1", "P2", "A1"], "afecta_indirecta": [], "afectado_por_indirecta": ["R12"]},
    "R11": {"afecta": ["R12"], "afectado_por": [], "afecta_indirecta": ["E8"], "afectado_por_indirecta": []},
    "R13": {"afecta": ["S8"], "afectado_por": ["R12", "E8"], "afecta_indirecta": [], "afectado_por_indirecta": []},
}


@lru_cache
def _base() -> dict:
    with open(Path(__file__).with_name("perlas_base.json"), encoding="utf-8") as f:
        return json.load(f)


def estrategias(codigo: str) -> list[str]:
    return _base()["estrategias"].get(codigo) or ESTRATEGIAS_ADICIONALES.get(codigo, [])


def interrelacion(codigo: str) -> dict[str, list[str]]:
    vacia = {"afecta": [], "afectado_por": [], "afecta_indirecta": [], "afectado_por_indirecta": []}
    rel = _base()["interrelacion"].get(codigo) or INTERRELACION_ADICIONAL.get(codigo) or {}
    return {**vacia, **rel}


def plan_de_accion(resultado: dict) -> list[dict]:
    """Prioriza los indicadores deficientes y en alerta.

    La prioridad considera el efecto "palanca": un indicador que afecta a
    muchos otros (y en especial a otros deficientes) se atiende primero.
    También identifica las causas probables: indicadores que lo afectan y que
    también están fuera de meta.
    """
    por_codigo = resultado["por_codigo"]
    fuera = {f["codigo"] for f in resultado["filas"] if f["estatus"] in ("deficiente", "alerta")}
    plan = []
    for f in resultado["filas"]:
        if f["estatus"] not in ("deficiente", "alerta"):
            continue
        rel = interrelacion(f["codigo"])
        afecta = set(rel["afecta"]) | set(rel["afecta_indirecta"])
        causas = [c for c in rel["afectado_por"] + rel["afectado_por_indirecta"] if c in fuera and c != f["codigo"]]
        arrastra = [c for c in afecta if c in fuera and c != f["codigo"]]
        puntaje = (
            (3 if f["estatus"] == "deficiente" else 1)
            + 2 * len(rel["afecta"])
            + len(rel["afecta_indirecta"])
            + 3 * len(arrastra)
        )
        plan.append(
            {
                "fila": f,
                "codigo": f["codigo"],
                "relacion": rel,
                "causas": list(dict.fromkeys(causas)),
                "arrastra": sorted(arrastra),
                "puntaje": puntaje,
                "estrategias": estrategias(f["codigo"]),
                "nombres": {c: por_codigo[c]["ind"].nombre for c in set(causas) | set(arrastra) if c in por_codigo},
            }
        )
    # Primero los deficientes (por efecto palanca) y después los que están en alerta.
    plan.sort(key=lambda x: (x["fila"]["estatus"] != "deficiente", -x["puntaje"]))
    n_def = sum(1 for p in plan if p["fila"]["estatus"] == "deficiente")
    for i, p in enumerate(plan, start=1):
        if p["fila"]["estatus"] != "deficiente":
            p["prioridad"] = "Seguimiento"
        else:
            p["prioridad"] = "Alta" if i <= max(3, round(n_def / 3)) else "Media"
    return plan
