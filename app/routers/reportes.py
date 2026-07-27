"""Reportes: ejecutivo, distribución de cartera y personalizados."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import consultas
from ..database import get_db
from ..models import ResultadoRiesgo
from ..plantillas import templates
from ..riesgo.provisionamiento import calcular_provisionamiento

router = APIRouter(prefix="/reportes", tags=["reportes"])


def _ultimo_var(db: Session, periodo: str) -> dict | None:
    r = (
        db.query(ResultadoRiesgo)
        .filter(ResultadoRiesgo.tipo == "var", ResultadoRiesgo.periodo == periodo)
        .order_by(ResultadoRiesgo.fecha.desc())
        .first()
    )
    return json.loads(r.resultados) if r else None


@router.get("/ejecutivo")
def ejecutivo(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    ctx = {
        "periodos": consultas.periodos_disponibles(db),
        "periodo": consultas.periodo_actual(db, periodo),
        "fecha": datetime.now(),
    }
    if not ctx["periodo"]:
        return templates.TemplateResponse(
            request, "reporte_ejecutivo.html", {**ctx, "hay_datos": False}
        )

    periodo_sel = ctx["periodo"]
    evolucion = consultas.evolucion_historica(db)
    actual = next((f for f in evolucion if f["periodo"] == periodo_sel), None)
    provision = calcular_provisionamiento(db, periodo_sel)
    var = _ultimo_var(db, periodo_sel)
    escenario_base = None
    if var:
        escenario_base = next((e for e in var.get("escenarios", []) if e.get("factor") == 1.0), None)

    por_producto, _ = consultas.distribucion(db, periodo_sel, "producto")
    por_sector, _ = consultas.distribucion(db, periodo_sel, "sector")
    por_region, _ = consultas.distribucion(db, periodo_sel, "region")

    return templates.TemplateResponse(
        request,
        "reporte_ejecutivo.html",
        {
            **ctx,
            "hay_datos": True,
            "actual": actual,
            "evolucion": evolucion[-6:],
            "provision": provision,
            "var": var,
            "escenario_base": escenario_base,
            "por_producto": por_producto[:5],
            "por_sector": por_sector[:5],
            "por_region": por_region,
        },
    )


@router.get("/distribucion")
def distribucion(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    ctx = {
        "periodos": consultas.periodos_disponibles(db),
        "periodo": consultas.periodo_actual(db, periodo),
        "fecha": datetime.now(),
    }
    tablas = []
    if ctx["periodo"]:
        for dimension, titulo in consultas.DIMENSIONES.items():
            filas, total = consultas.distribucion(db, ctx["periodo"], dimension)
            tablas.append({"titulo": titulo, "filas": filas, "total": total})
    return templates.TemplateResponse(
        request, "reporte_distribucion.html", {**ctx, "tablas": tablas}
    )


@router.get("/personalizado")
def personalizado(
    request: Request,
    periodo: str | None = None,
    dimension: str = "producto",
    orden: str = "total",
    limite: int = 0,
    db: Session = Depends(get_db),
):
    if dimension not in consultas.DIMENSIONES:
        dimension = "producto"
    ctx = {
        "periodos": consultas.periodos_disponibles(db),
        "periodo": consultas.periodo_actual(db, periodo),
        "dimension": dimension,
        "dimensiones": consultas.DIMENSIONES,
        "orden": orden,
        "limite": limite,
    }
    filas, total = ([], None)
    if ctx["periodo"]:
        filas, total = consultas.distribucion(db, ctx["periodo"], dimension)
        llaves_orden = {
            "total": lambda f: f["total"],
            "vigente": lambda f: f["saldo_vigente"],
            "vencido": lambda f: f["saldo_vencido"],
            "creditos": lambda f: f["creditos"],
            "imor": lambda f: f["imor"],
        }
        filas.sort(key=llaves_orden.get(orden, llaves_orden["total"]), reverse=True)
        if limite and limite > 0:
            filas = filas[:limite]
    return templates.TemplateResponse(
        request, "reporte_personalizado.html", {**ctx, "filas": filas, "total": total}
    )


@router.get("/personalizado.csv")
def personalizado_csv(
    periodo: str | None = None,
    dimension: str = "producto",
    db: Session = Depends(get_db),
):
    if dimension not in consultas.DIMENSIONES:
        dimension = "producto"
    periodo_sel = consultas.periodo_actual(db, periodo)
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(
        [consultas.DIMENSIONES[dimension], "Créditos", "Saldo Vigente", "Saldo Vencido", "Total", "Participación %", "IMOR %"]
    )
    if periodo_sel:
        filas, total = consultas.distribucion(db, periodo_sel, dimension)
        for f in filas:
            escritor.writerow(
                [
                    f["grupo"],
                    f["creditos"],
                    round(f["saldo_vigente"], 2),
                    round(f["saldo_vencido"], 2),
                    round(f["total"], 2),
                    round(f["participacion"], 2),
                    round(f["imor"], 2),
                ]
            )
        escritor.writerow(
            ["TOTAL", total["creditos"], round(total["saldo_vigente"], 2), round(total["saldo_vencido"], 2), round(total["total"], 2), 100.0, round(total["imor"], 2)]
        )
    salida.seek(0)
    nombre = f"reporte_{dimension}_{periodo_sel or 'sin_periodo'}.csv"
    return StreamingResponse(
        iter([salida.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )
