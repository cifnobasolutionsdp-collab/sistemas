"""Portal de suscripciones para organizaciones financieras — cifnoba.com.

Plataforma donde SOCAPS, SOFIPOS y SOFOMES se registran y suscriben para
acceder al sistema de reclutamiento con postulación conversacional Fast Apply.

Ejecución:  uvicorn portal.main:app --reload --port 8002
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .plantillas import templates
from .routers import auth, panel

Base.metadata.create_all(bind=engine)

app = FastAPI(title="cifnoba.com — Portal de Reclutamiento para Instituciones Financieras")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(auth.router)
app.include_router(panel.router)


@app.get("/")
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})
