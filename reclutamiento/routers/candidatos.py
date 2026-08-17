"""Gestión de candidatos: listado, detalle con conversación, CV autogenerado
y cambio de estatus (preseleccionar, descartar, contratar)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..chatbot import generar_cv
from ..database import get_db
from ..plantillas import templates

router = APIRouter(prefix="/candidatos", tags=["candidatos"])


def _postulacion(db: Session, postulacion_id: int) -> models.Postulacion:
    postulacion = db.get(models.Postulacion, postulacion_id)
    if postulacion is None:
        raise HTTPException(status_code=404, detail="Candidato no encontrado")
    return postulacion


@router.get("")
def listar(
    request: Request,
    proceso_id: int | None = None,
    estado: str = "",
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Postulacion).order_by(models.Postulacion.iniciada_en.desc())
    if proceso_id:
        consulta = consulta.filter(models.Postulacion.proceso_id == proceso_id)
    if estado:
        consulta = consulta.filter(models.Postulacion.estado == estado)
    postulaciones = consulta.all()
    procesos = db.query(models.Proceso).order_by(models.Proceso.posicion).all()
    return templates.TemplateResponse(
        request,
        "candidatos_lista.html",
        {
            "postulaciones": postulaciones,
            "procesos": procesos,
            "proceso_id": proceso_id,
            "estado": estado,
        },
    )


@router.get("/{postulacion_id}")
def detalle(postulacion_id: int, request: Request, db: Session = Depends(get_db)):
    postulacion = _postulacion(db, postulacion_id)
    return templates.TemplateResponse(
        request,
        "candidato_detalle.html",
        {"postulacion": postulacion, "cv": generar_cv(postulacion)},
    )


@router.get("/{postulacion_id}/cv")
def cv(postulacion_id: int, request: Request, db: Session = Depends(get_db)):
    postulacion = _postulacion(db, postulacion_id)
    return templates.TemplateResponse(
        request,
        "candidato_cv.html",
        {"postulacion": postulacion, "cv": generar_cv(postulacion)},
    )


@router.post("/{postulacion_id}/estado")
def cambiar_estado(
    postulacion_id: int, estado: str = Form(...), db: Session = Depends(get_db)
):
    postulacion = _postulacion(db, postulacion_id)
    if estado in models.ESTADOS_POSTULACION and estado != "en_curso":
        postulacion.estado = estado
        db.commit()
    return RedirectResponse(f"/candidatos/{postulacion.id}", status_code=303)
