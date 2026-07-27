"""Cálculo de provisionamiento (reservas preventivas) de la cartera.

Metodología parametrizable: cada crédito se califica según sus días de mora
conforme al catálogo de Calificaciones de Crédito y se le aplica el
porcentaje de reserva del catálogo de Reservas Preventivas. Los porcentajes
sembrados son de referencia y deben ajustarse a la disposición vigente de la
CNBV aplicable a la entidad (SOCAP o SOFOM).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import CalificacionCredito, Prestamo, ReservaPreventiva


def clasificar_por_mora(dias_mora: int, calificaciones: list[CalificacionCredito]) -> CalificacionCredito | None:
    """Devuelve la calificación cuyo rango de días de mora contiene ``dias_mora``."""
    for calif in calificaciones:
        if dias_mora >= calif.mora_min and (calif.mora_max is None or dias_mora <= calif.mora_max):
            return calif
    return calificaciones[-1] if calificaciones else None


def calcular_provisionamiento(db: Session, periodo: str) -> dict:
    """Calcula reservas preventivas del periodo, desglosadas por calificación."""
    calificaciones = (
        db.query(CalificacionCredito).order_by(CalificacionCredito.mora_min).all()
    )
    pct_reserva = {
        r.calificacion_id: r.porcentaje_reserva for r in db.query(ReservaPreventiva).all()
    }
    prestamos = db.query(Prestamo).filter(Prestamo.periodo == periodo).all()

    desglose: dict[str, dict] = {}
    for calif in calificaciones:
        desglose[calif.clave] = {
            "calificacion": calif.clave,
            "descripcion": calif.descripcion,
            "rango_mora": f"{calif.mora_min} - {calif.mora_max if calif.mora_max is not None else '∞'}",
            "porcentaje_reserva": pct_reserva.get(calif.id, 0.0),
            "creditos": 0,
            "exposicion": 0.0,
            "reserva": 0.0,
        }

    sin_calificar = 0
    for p in prestamos:
        calif = clasificar_por_mora(p.dias_mora or 0, calificaciones)
        if calif is None:
            sin_calificar += 1
            continue
        fila = desglose[calif.clave]
        exposicion = p.exposicion
        fila["creditos"] += 1
        fila["exposicion"] += exposicion
        fila["reserva"] += exposicion * pct_reserva.get(calif.id, 0.0) / 100.0

    total_exposicion = sum(f["exposicion"] for f in desglose.values())
    total_reserva = sum(f["reserva"] for f in desglose.values())
    saldo_vencido = sum(p.saldo_vencido or 0.0 for p in prestamos)

    return {
        "periodo": periodo,
        "creditos": len(prestamos),
        "sin_calificar": sin_calificar,
        "desglose": list(desglose.values()),
        "total_exposicion": total_exposicion,
        "total_reserva": total_reserva,
        "porcentaje_reserva_cartera": (total_reserva / total_exposicion * 100.0) if total_exposicion else 0.0,
        "saldo_vencido": saldo_vencido,
        "icor": (total_reserva / saldo_vencido * 100.0) if saldo_vencido else 0.0,
    }
