"""Cálculo de VaR de crédito, pérdida esperada/no esperada y concentración.

Modelo de simulación Monte Carlo por incumplimiento:

* Para cada crédito ``i``: EAD_i = saldo vigente + saldo vencido,
  PI_i = probabilidad de incumplimiento de su calificación (por días de mora),
  SP_i = severidad de la pérdida ajustada por la cobertura de su garantía.
* Pérdida Esperada  (PE) = Σ PI_i · SP_i · EAD_i
* En cada simulación, cada crédito incumple con probabilidad PI_i y la
  pérdida del escenario es Σ SP_i · EAD_i de los incumplidos.
* VaR(α) = percentil α de la distribución simulada de pérdidas.
* Pérdida No Esperada (PNE) = VaR(α) − PE.
* Escenarios de estrés: se recalcula todo multiplicando las PI por un factor
  (con tope de 100 %).
* Índice de concentración: Herfindahl-Hirschman (IHH) sobre la participación
  de cada acreditado en la exposición total, e IHH por dimensión.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

from sqlalchemy.orm import Session

from ..models import CalificacionCredito, Prestamo
from .provisionamiento import clasificar_por_mora


def _percentil(valores_ordenados: list[float], alfa: float) -> float:
    if not valores_ordenados:
        return 0.0
    n = len(valores_ordenados)
    indice = min(max(int(math.ceil(alfa * n)) - 1, 0), n - 1)
    return valores_ordenados[indice]


def indice_herfindahl(exposiciones: list[float]) -> float:
    """IHH en escala 0-10,000 (10,000 = concentración total)."""
    total = sum(exposiciones)
    if not total:
        return 0.0
    return sum((e / total) ** 2 for e in exposiciones) * 10_000


def _construir_posiciones(db: Session, periodo: str) -> list[dict]:
    calificaciones = (
        db.query(CalificacionCredito).order_by(CalificacionCredito.mora_min).all()
    )
    posiciones = []
    for p in db.query(Prestamo).filter(Prestamo.periodo == periodo).all():
        ead = p.exposicion
        if ead <= 0:
            continue
        calif = clasificar_por_mora(p.dias_mora or 0, calificaciones)
        pi = (calif.probabilidad_incumplimiento if calif else 100.0) / 100.0
        severidad = (calif.severidad if calif else 100.0) / 100.0
        cobertura = (p.garantia.porcentaje_cobertura if p.garantia else 0.0) / 100.0
        sp = max(severidad * (1.0 - cobertura), 0.0)
        posiciones.append(
            {
                "prestamo": p,
                "socio": p.socio,
                "ead": ead,
                "pi": min(pi, 1.0),
                "sp": sp,
            }
        )
    return posiciones


def _simular(posiciones: list[dict], factor_pi: float, simulaciones: int, rng: random.Random) -> list[float]:
    perdidas = []
    parametros = [
        (min(pos["pi"] * factor_pi, 1.0), pos["sp"] * pos["ead"]) for pos in posiciones
    ]
    for _ in range(simulaciones):
        perdida = 0.0
        azar = rng.random
        for pi, perdida_incumplimiento in parametros:
            if azar() < pi:
                perdida += perdida_incumplimiento
        perdidas.append(perdida)
    perdidas.sort()
    return perdidas


def _histograma(perdidas: list[float], bins: int = 20) -> list[dict]:
    if not perdidas:
        return []
    minimo, maximo = perdidas[0], perdidas[-1]
    ancho = (maximo - minimo) / bins or 1.0
    conteos = [0] * bins
    for p in perdidas:
        i = min(int((p - minimo) / ancho), bins - 1)
        conteos[i] += 1
    total = len(perdidas)
    return [
        {
            "desde": minimo + i * ancho,
            "hasta": minimo + (i + 1) * ancho,
            "conteo": c,
            "porcentaje": c / total * 100.0,
        }
        for i, c in enumerate(conteos)
    ]


def calcular_var(
    db: Session,
    periodo: str,
    confianza: float = 0.99,
    simulaciones: int = 2000,
    factores_estres: tuple[float, ...] = (1.0, 1.5, 2.0),
    semilla: int = 20260101,
) -> dict:
    """Calcula PE, PNE, VaR e IHH del periodo, con escenarios de estrés."""
    posiciones = _construir_posiciones(db, periodo)
    exposicion_total = sum(pos["ead"] for pos in posiciones)
    rng = random.Random(semilla)

    escenarios = []
    histograma_base: list[dict] = []
    for factor in factores_estres:
        perdida_esperada = sum(
            min(pos["pi"] * factor, 1.0) * pos["sp"] * pos["ead"] for pos in posiciones
        )
        perdidas = _simular(posiciones, factor, simulaciones, rng)
        var = _percentil(perdidas, confianza)
        escenarios.append(
            {
                "factor": factor,
                "nombre": "Base" if factor == 1.0 else f"Estrés x{factor:g}",
                "perdida_esperada": perdida_esperada,
                "var": var,
                "perdida_no_esperada": max(var - perdida_esperada, 0.0),
                "perdida_maxima": perdidas[-1] if perdidas else 0.0,
                "pe_sobre_cartera": (perdida_esperada / exposicion_total * 100.0) if exposicion_total else 0.0,
                "var_sobre_cartera": (var / exposicion_total * 100.0) if exposicion_total else 0.0,
            }
        )
        if factor == 1.0:
            histograma_base = _histograma(perdidas)

    # Concentración por acreditado y por dimensiones relevantes
    por_socio: dict[str, float] = defaultdict(float)
    por_dimension: dict[str, dict[str, float]] = {
        "Producto": defaultdict(float),
        "Sucursal": defaultdict(float),
        "Sector Económico": defaultdict(float),
        "Región": defaultdict(float),
    }
    for pos in posiciones:
        p = pos["prestamo"]
        por_socio[pos["socio"]] += pos["ead"]
        por_dimension["Producto"][p.producto.nombre] += pos["ead"]
        por_dimension["Sucursal"][p.sucursal.nombre] += pos["ead"]
        por_dimension["Sector Económico"][p.actividad.sector_economico] += pos["ead"]
        por_dimension["Región"][p.sucursal.plaza.region.nombre] += pos["ead"]

    ihh_dimensiones = [
        {"dimension": nombre, "ihh": indice_herfindahl(list(valores.values()))}
        for nombre, valores in por_dimension.items()
    ]
    mayores = sorted(por_socio.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "periodo": periodo,
        "confianza": confianza,
        "simulaciones": simulaciones,
        "creditos": len(posiciones),
        "exposicion_total": exposicion_total,
        "escenarios": escenarios,
        "histograma": histograma_base,
        "ihh_acreditados": indice_herfindahl(list(por_socio.values())),
        "ihh_dimensiones": ihh_dimensiones,
        "mayores_acreditados": [
            {
                "socio": socio,
                "exposicion": monto,
                "porcentaje": (monto / exposicion_total * 100.0) if exposicion_total else 0.0,
            }
            for socio, monto in mayores
        ],
    }
