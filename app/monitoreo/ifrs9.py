"""Pérdida crediticia esperada (PCE / ECL) con enfoque IFRS 9.

Modelo simplificado por etapas, útil para *monitoreo* cuando la entidad no
reporta su propia PCE:

    PCE_etapa = EAD_etapa × PD_etapa × LGD × factor prospectivo

* Etapa 1: PD a 12 meses.
* Etapa 2: PD de vida remanente (incremento significativo del riesgo).
* Etapa 3: PD = 100 % (crédito deteriorado).
* El factor prospectivo (*forward looking*) es el promedio ponderado de los
  multiplicadores de PD de los escenarios macroeconómicos.

Si la entidad reporta su PCE por etapa (rubros ``pe_etapa1..3``) se utiliza
esa cifra. Los parámetros son de referencia y deben calibrarse con la
experiencia de pérdida de cada entidad y la metodología vigente de la CNBV.
"""
from __future__ import annotations

import copy

PARAMETROS_POR_OMISION = {
    "pd_etapa1": 0.03,
    "pd_etapa2": 0.25,
    "pd_etapa3": 1.0,
    "lgd": 0.45,
    "escenarios": [
        {"nombre": "Base", "peso": 0.60, "factor": 1.00},
        {"nombre": "Optimista", "peso": 0.15, "factor": 0.85},
        {"nombre": "Pesimista", "peso": 0.25, "factor": 1.35},
    ],
}


def parametros(personalizados: dict | None) -> dict:
    p = copy.deepcopy(PARAMETROS_POR_OMISION)
    for k, v in (personalizados or {}).items():
        if k in p and v not in (None, ""):
            p[k] = v
    return p


def factor_prospectivo(escenarios: list[dict]) -> float:
    peso = sum(float(e["peso"]) for e in escenarios) or 1.0
    return sum(float(e["peso"]) * float(e["factor"]) for e in escenarios) / peso


def calcular_pce(datos: dict[str, float], params: dict | None = None) -> dict:
    p = parametros(params)
    g = lambda k: float(datos.get(k) or 0.0)  # noqa: E731
    factor = factor_prospectivo(p["escenarios"])
    cartera = [g("cartera_etapa1"), g("cartera_etapa2"), g("cartera_etapa3")]
    total_cartera = sum(cartera)
    pds = [float(p["pd_etapa1"]), float(p["pd_etapa2"]), float(p["pd_etapa3"])]
    lgd = float(p["lgd"])

    def pce_con(f: float) -> list[float]:
        return [ead * min(1.0, pd * f) * lgd for ead, pd in zip(cartera, pds)]

    pce_modelo = pce_con(factor)
    propia = [g("pe_etapa1"), g("pe_etapa2"), g("pe_etapa3")]
    usa_propia = any(propia)
    pce = propia if usa_propia else pce_modelo

    reservas = [g("reserva_etapa1"), g("reserva_etapa2"), g("reserva_etapa3")]
    asignacion_estimada = not any(reservas)
    if asignacion_estimada:
        # Se asigna la EPRC total primero a etapa 3, luego 2 y el remanente a etapa 1.
        restante = g("estimaciones")
        reservas = [0.0, 0.0, 0.0]
        for i in (2, 1):
            reservas[i] = min(restante, pce[i])
            restante -= reservas[i]
        reservas[0] = restante

    etapas = []
    for i in range(3):
        etapas.append(
            {
                "etapa": i + 1,
                "cartera": cartera[i],
                "participacion": cartera[i] / total_cartera if total_cartera else None,
                "pd": min(1.0, pds[i] * factor),
                "pce": pce[i],
                "reserva": reservas[i],
                "cobertura": reservas[i] / cartera[i] if cartera[i] else None,
                "suficiencia": reservas[i] / pce[i] if pce[i] else None,
                "deficit": max(0.0, pce[i] - reservas[i]),
            }
        )
    total_pce = sum(pce)
    total_reserva = sum(reservas)
    escenarios = []
    for e in p["escenarios"]:
        valor = sum(pce_con(float(e["factor"])))
        escenarios.append({**e, "pce": valor, "deficit": max(0.0, valor - total_reserva)})
    return {
        "parametros": p,
        "factor": factor,
        "lgd": lgd,
        "etapas": etapas,
        "cartera_total": total_cartera,
        "pce_total": total_pce,
        "reserva_total": total_reserva,
        "suficiencia": total_reserva / total_pce if total_pce else None,
        "deficit": max(0.0, total_pce - total_reserva),
        "excedente": max(0.0, total_reserva - total_pce),
        "fuente_pce": "Reportada por la entidad" if usa_propia else "Modelo de referencia PD × LGD × EAD",
        "asignacion_estimada": asignacion_estimada,
        "escenarios": escenarios,
    }
