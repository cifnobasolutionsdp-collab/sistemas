"""Consultas de cartera: plazos, montos, evolución, distribución y límites."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .. import consultas
from ..database import get_db
from ..plantillas import templates

router = APIRouter(prefix="/consultas", tags=["consultas"])


def _contexto_periodo(db: Session, periodo: str | None) -> dict:
    return {
        "periodos": consultas.periodos_disponibles(db),
        "periodo": consultas.periodo_actual(db, periodo),
    }


@router.get("/plazo")
def por_plazo(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    ctx = _contexto_periodo(db, periodo)
    filas, total = ([], None)
    if ctx["periodo"]:
        filas, total = consultas.prestamos_por_plazo(db, ctx["periodo"])
    return templates.TemplateResponse(
        request,
        "consulta_buckets.html",
        {
            **ctx,
            "titulo": "Préstamos otorgados por plazo",
            "columna_grupo": "Plazo",
            "ruta": "/consultas/plazo",
            "filas": filas,
            "total": total,
        },
    )


@router.get("/monto")
def por_monto(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    ctx = _contexto_periodo(db, periodo)
    filas, total = ([], None)
    if ctx["periodo"]:
        filas, total = consultas.prestamos_por_monto(db, ctx["periodo"])
    return templates.TemplateResponse(
        request,
        "consulta_buckets.html",
        {
            **ctx,
            "titulo": "Préstamos otorgados por monto",
            "columna_grupo": "Rango de monto",
            "ruta": "/consultas/monto",
            "filas": filas,
            "total": total,
        },
    )


@router.get("/evolucion")
def evolucion(request: Request, db: Session = Depends(get_db)):
    filas = consultas.evolucion_historica(db)
    max_total = max((f["total"] for f in filas), default=0.0) or 1.0
    return templates.TemplateResponse(
        request, "consulta_evolucion.html", {"filas": filas, "max_total": max_total}
    )


@router.get("/distribucion")
def distribucion(
    request: Request,
    dimension: str = "producto",
    periodo: str | None = None,
    db: Session = Depends(get_db),
):
    if dimension not in consultas.DIMENSIONES:
        dimension = "producto"
    ctx = _contexto_periodo(db, periodo)
    filas, total = ([], None)
    if ctx["periodo"]:
        filas, total = consultas.distribucion(db, ctx["periodo"], dimension)
    return templates.TemplateResponse(
        request,
        "consulta_distribucion.html",
        {
            **ctx,
            "dimension": dimension,
            "dimensiones": consultas.DIMENSIONES,
            "filas": filas,
            "total": total,
        },
    )


@router.get("/limites")
def limites(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    ctx = _contexto_periodo(db, periodo)
    seguimiento = consultas.seguimiento_limites(db, ctx["periodo"]) if ctx["periodo"] else []
    individuales = [s for s in seguimiento if s["limite"].tipo == "Individual"]
    generales = [s for s in seguimiento if s["limite"].tipo == "General"]
    return templates.TemplateResponse(
        request,
        "consulta_limites.html",
        {**ctx, "individuales": individuales, "generales": generales},
    )
