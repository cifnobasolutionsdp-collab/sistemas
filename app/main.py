"""Sistema de Administración de Riesgos de Crédito para SOCAPS y SOFOMES.

Aplicación web con módulos de catálogos, consultas, procesos y reportes,
orientada al cumplimiento de la Ley de Instituciones de Crédito, la LRASCAP
y las disposiciones de la CNBV en materia de riesgo de crédito.
"""
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import consultas
from .database import Base, engine, get_db
from .plantillas import templates
from .riesgo.provisionamiento import calcular_provisionamiento
from .routers import catalogos, consultas as consultas_router, procesos, reportes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Administración de Riesgos de Crédito — SOCAPS / SOFOMES")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(catalogos.router)
app.include_router(consultas_router.router)
app.include_router(procesos.router)
app.include_router(reportes.router)


@app.get("/")
def inicio(request: Request, db: Session = Depends(get_db)):
    periodo = consultas.periodo_actual(db)
    resumen = None
    provision = None
    if periodo:
        evolucion = consultas.evolucion_historica(db)
        resumen = next((f for f in evolucion if f["periodo"] == periodo), None)
        provision = calcular_provisionamiento(db, periodo)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"periodo": periodo, "resumen": resumen, "provision": provision},
    )
