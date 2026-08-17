"""Sistema de Reclutamiento y Selección para SOCAPS, SOFIPOS y SOFOMES.

Aplicación web de atracción de talento con postulación conversacional exprés
(«Fast Apply»): procesos de vacantes con preguntas de filtro ponderadas,
chatbot configurable, CV autogenerado, nivel de adecuación, publicación
multicanal con código QR y tablero de indicadores de contratación.

Ejecución:  uvicorn reclutamiento.main:app --reload --port 8001
"""
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine, get_db
from .plantillas import templates
from .routers import candidatos, catalogos, postulacion, procesos

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Reclutamiento y Selección — SOCAPS / SOFIPOS / SOFOMES")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(procesos.router)
app.include_router(candidatos.router)
app.include_router(postulacion.router)
app.include_router(catalogos.router)


@app.get("/")
def inicio(request: Request, db: Session = Depends(get_db)):
    procesos_todos = db.query(models.Proceso).all()
    activos = [p for p in procesos_todos if p.estado == "publicado"]
    total_postulaciones = db.query(func.count(models.Postulacion.id)).scalar() or 0
    completadas = (
        db.query(models.Postulacion)
        .filter(models.Postulacion.completada_en.isnot(None))
        .all()
    )
    contratados = [p for p in completadas if p.estado == "contratado"]
    preseleccionados = [p for p in completadas if p.estado == "preseleccionado"]
    adecuaciones = [p.adecuacion for p in completadas if p.adecuacion is not None]
    duraciones = [p.duracion_minutos for p in completadas if p.duracion_minutos is not None]

    indicadores = {
        "procesos_activos": len(activos),
        "procesos_totales": len(procesos_todos),
        "postulaciones": total_postulaciones,
        "postulados": len([p for p in completadas if p.estado == "postulado"]),
        "preseleccionados": len(preseleccionados),
        "contratados": len(contratados),
        "descartados": len([p for p in completadas if p.estado == "descartado"]),
        "adecuacion_promedio": (sum(adecuaciones) / len(adecuaciones)) if adecuaciones else None,
        "minutos_promedio": (sum(duraciones) / len(duraciones)) if duraciones else None,
    }
    recientes = (
        db.query(models.Postulacion)
        .order_by(models.Postulacion.iniciada_en.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {"indicadores": indicadores, "procesos": procesos_todos, "recientes": recientes},
    )
