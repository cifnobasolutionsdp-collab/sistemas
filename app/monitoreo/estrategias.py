"""Estrategias de mejora, interrelación de indicadores y plan de acción.

Las estrategias e interrelaciones de los indicadores financieros provienen
del archivo de referencia proporcionado. Se complementan con estrategias para los
indicadores IFRS 9 (pérdida crediticia esperada) y de solvencia/eficiencia.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ESTRATEGIAS_ADICIONALES: dict[str, list[str]] = {
    "Z2": ["Seguir las estrategias mencionadas en O2, Inversiones líquidas: canalizar los excedentes de liquidez a cartera de crédito sana conforme al plan de tesorería."],
    "Z3": ["Seguir las estrategias mencionadas en O3, Inversiones financieras, privilegiando instrumentos seguros y de plazo congruente con el calce de pasivos."],
    "Z4": ["Seguir las estrategias mencionadas en O4, Inversiones no financieras: no incrementar activos que no generen rendimiento financiero."],
    "Z9": ["Seguir las estrategias mencionadas en O9, Capital institucional neto: capitalizar excedentes y cubrir al 100 % la cartera en riesgo con estimaciones."],
    "I11": ["Reducir partidas extraordinarias; documentar y analizar mensualmente los otros ingresos y gastos para que no distorsionen el excedente operativo."],
    "I13": ["Mejorar el ROA (I12) mediante margen bruto suficiente (I8) y control de gastos (I9).", "Capitalizar a la reserva los excedentes para que el capital institucional crezca en términos reales."],
    "D1": [
        "Fortalecer la originación: análisis de capacidad de pago, historial en sociedades de información crediticia y scoring por producto.",
        "Monitorear alertas tempranas (primer atraso, reestructuras, sobreendeudamiento) para evitar la migración a etapa 2.",
        "Diseñar productos y plazos acordes al flujo del acreditado para mantener la cartera al corriente.",
    ],
    "D2": [
        "Definir y documentar el criterio de incremento significativo del riesgo (p. ej. > 30 días de atraso, reestructura, deterioro en buró) y aplicarlo de forma consistente.",
        "Gestión de cobranza preventiva sobre la cartera de etapa 2 para regresarla a etapa 1 (curas) antes de que llegue a deterioro.",
        "Restringir renovaciones y reestructuras que sólo difieren el reconocimiento del deterioro.",
    ],
    "D3": [
        "Seguir las estrategias de E1 (morosidad): cobranza extrajudicial y judicial oportuna, unidad especializada de recuperación.",
        "Depurar (castigar) la cartera deteriorada totalmente reservada conforme a la política aprobada por el Consejo (S3/S4).",
        "Analizar cosechas (vintage) por producto, sucursal y promotor para corregir originación deficiente.",
    ],
    "D4": [
        "Constituir mensualmente la PCE a 12 meses de la cartera etapa 1 con PD calibradas a la experiencia histórica de la entidad.",
        "Incorporar información prospectiva (escenarios macroeconómicos) en la PD, revisando trimestralmente sus ponderaciones.",
    ],
    "D5": [
        "Reconocer la PCE por toda la vida del crédito para la cartera de etapa 2.",
        "Revisar la LGD por tipo de garantía (líquida, hipotecaria, prendaria, sin garantía) para que la reserva refleje la recuperación esperada.",
    ],
    "D6": [
        "Reservar la cartera etapa 3 al nivel de su pérdida esperada (PD = 100 %), descontando sólo garantías ejecutables y valuadas.",
        "Destinar las recuperaciones de cartera castigada (S5) a fortalecer la estimación.",
    ],
    "D7": [
        "Cubrir el déficit de reservas contra la PCE con cargo a resultados de forma gradual y programada, informando al Consejo y a la autoridad.",
        "Ajustar la tasa activa para incorporar el costo de riesgo (prima por pérdida esperada) en el precio de los créditos (I1).",
        "Priorizar la aplicación del excedente: primero estimaciones, luego capitalización y por último distribución.",
    ],
    "D8": ["Seguir las estrategias de D6 e D7: la EPRC total debe cubrir al menos el 100 % de la cartera deteriorada."],
    "D9": [
        "Reducir el costo de riesgo mejorando la originación (scoring, capacidad de pago) y la cobranza temprana.",
        "Fijar precios ajustados por riesgo: la tasa activa debe cubrir costo de fondeo + gastos operativos + pérdida esperada + margen para capital.",
    ],
    "D10": [
        "Dar seguimiento mensual a la matriz de transición entre etapas (1→2, 2→3 y curas) por producto y sucursal.",
        "Activar planes de cobranza preventiva sobre los segmentos con mayor migración.",
    ],
    "D11": [
        "Capitalizar excedentes y, en su caso, aportaciones adicionales para absorber el déficit de reservas IFRS 9 sin bajar del 10 % de capital/activo.",
        "Elaborar un plan de transición para el reconocimiento del déficit que preserve el nivel de capitalización requerido por la regulación.",
    ],
    "O10": [
        "Reducir el apalancamiento capitalizando utilidades y/o con aportaciones de capital de los accionistas.",
        "Diversificar y escalonar el fondeo (banca de desarrollo, emisiones, líneas revolventes) para evitar concentraciones de vencimientos.",
    ],
    "I14": [
        "Controlar el gasto mediante presupuesto autorizado y seguimiento mensual de desviaciones (I9).",
        "Digitalizar procesos de originación y cobranza para lograr economías de escala.",
        "Incrementar el margen bruto (I8) ajustando tasas activas y pasivas.",
    ],
}

INTERRELACION_ADICIONAL: dict[str, dict[str, list[str]]] = {
    "D1": {"afecta": ["D4", "D7", "E1", "I10"], "afectado_por": ["D2", "D3", "Z1"], "afecta_indirecta": ["I12", "O8"], "afectado_por_indirecta": ["I1"]},
    "D2": {"afecta": ["D5", "D7", "I10", "D10"], "afectado_por": ["E1", "Z1"], "afecta_indirecta": ["I12", "O8", "D11"], "afectado_por_indirecta": ["I1"]},
    "D3": {"afecta": ["E1", "D6", "D7", "D8", "I10", "S1", "S2"], "afectado_por": ["S3", "S4", "D2"], "afecta_indirecta": ["I12", "O8", "O9", "D11"], "afectado_por_indirecta": ["Z1"]},
    "D4": {"afecta": ["D7", "I10"], "afectado_por": ["D1", "I8"], "afecta_indirecta": ["I12"], "afectado_por_indirecta": []},
    "D5": {"afecta": ["D7", "I10"], "afectado_por": ["D2", "I8"], "afecta_indirecta": ["I12"], "afectado_por_indirecta": []},
    "D6": {"afecta": ["D7", "D8", "S1", "S2", "I10"], "afectado_por": ["D3", "S5", "I8"], "afecta_indirecta": ["I12", "O9"], "afectado_por_indirecta": []},
    "D7": {"afecta": ["D11", "I10", "I12", "O9"], "afectado_por": ["D4", "D5", "D6", "I8", "S5"], "afecta_indirecta": ["O8", "Z8"], "afectado_por_indirecta": ["E1"]},
    "D8": {"afecta": ["O9", "S6"], "afectado_por": ["D3", "I10"], "afecta_indirecta": ["D11"], "afectado_por_indirecta": []},
    "D9": {"afecta": ["I8", "I12", "I10"], "afectado_por": ["E1", "D2", "D3"], "afecta_indirecta": ["O8", "Z8"], "afectado_por_indirecta": ["Z1"]},
    "D10": {"afecta": ["D2", "D3", "D9"], "afectado_por": ["Z1", "E1"], "afecta_indirecta": ["I12"], "afectado_por_indirecta": []},
    "D11": {"afecta": ["O8", "S6"], "afectado_por": ["D7", "I12"], "afecta_indirecta": ["Z8"], "afectado_por_indirecta": []},
    "O10": {"afecta": ["O8", "I6"], "afectado_por": ["O6", "Z6", "I12"], "afecta_indirecta": ["I12"], "afectado_por_indirecta": []},
    "I14": {"afecta": ["I12", "O8"], "afectado_por": ["I8", "I9"], "afecta_indirecta": ["Z8"], "afectado_por_indirecta": []},
    "Z2": {"afecta": ["O2", "Z11"], "afectado_por": ["Z5", "Z1"], "afecta_indirecta": ["I8"], "afectado_por_indirecta": []},
    "Z3": {"afecta": ["O3", "Z11"], "afectado_por": ["Z5"], "afecta_indirecta": ["I8"], "afectado_por_indirecta": []},
    "Z4": {"afecta": ["O4", "E2"], "afectado_por": ["Z8"], "afecta_indirecta": ["I8"], "afectado_por_indirecta": []},
    "Z9": {"afecta": ["O9"], "afectado_por": ["Z8", "S1", "S2"], "afecta_indirecta": [], "afectado_por_indirecta": []},
    "S6": {"afecta": ["O9", "Z5"], "afectado_por": ["S1", "S2", "E1", "O8"], "afecta_indirecta": ["Z7"], "afectado_por_indirecta": ["I12"]},
    "O9": {"afecta": ["S6", "Z9"], "afectado_por": ["O8", "S1", "S2", "E1"], "afecta_indirecta": [], "afectado_por_indirecta": ["I12"]},
    "I11": {"afecta": ["I12"], "afectado_por": [], "afecta_indirecta": ["O8"], "afectado_por_indirecta": []},
    "I13": {"afecta": ["Z8"], "afectado_por": ["I12", "O8"], "afecta_indirecta": [], "afectado_por_indirecta": []},
}


@lru_cache
def _base() -> dict:
    with open(Path(__file__).with_name("indicadores_base.json"), encoding="utf-8") as f:
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
