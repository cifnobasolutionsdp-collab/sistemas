"""Postulación pública Fast Apply.

Experiencia conversacional del candidato (estilo WhatsApp): registro simple
sin formularios largos, solicitud opcional de currículum, preguntas de
filtro con avance o descarte automático y confirmación final con CV
autogenerado.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import chatbot, models
from ..database import get_db
from ..plantillas import templates

router = APIRouter(prefix="/postular", tags=["postulacion"])


def _proceso_por_token(db: Session, token: str) -> models.Proceso:
    proceso = (
        db.query(models.Proceso).filter(models.Proceso.token == token).one_or_none()
    )
    if proceso is None:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    return proceso


def _postulacion_valida(
    db: Session, proceso: models.Proceso, p: int | None
) -> models.Postulacion | None:
    if p is None:
        return None
    postulacion = db.get(models.Postulacion, p)
    if postulacion is None or postulacion.proceso_id != proceso.id:
        return None
    return postulacion


@router.get("/{token}")
def chat(token: str, request: Request, p: int | None = None, db: Session = Depends(get_db)):
    proceso = _proceso_por_token(db, token)
    postulacion = _postulacion_valida(db, proceso, p)
    if postulacion is None and not proceso.recibe_postulaciones:
        return templates.TemplateResponse(
            request, "postulacion_cerrada.html", {"proceso": proceso}, status_code=410
        )
    pregunta = chatbot.pregunta_actual(postulacion) if postulacion else None
    return templates.TemplateResponse(
        request,
        "postulacion_chat.html",
        {"proceso": proceso, "postulacion": postulacion, "pregunta": pregunta},
    )


@router.post("/{token}/iniciar")
def iniciar(
    token: str,
    nombre: str = Form(...),
    telefono: str = Form(""),
    correo: str = Form(""),
    db: Session = Depends(get_db),
):
    proceso = _proceso_por_token(db, token)
    if not proceso.recibe_postulaciones:
        raise HTTPException(status_code=410, detail="La vacante no recibe postulaciones")
    if not nombre.strip():
        raise HTTPException(status_code=422, detail="El nombre es obligatorio")
    postulacion = chatbot.iniciar_postulacion(db, proceso, nombre, telefono, correo)
    return RedirectResponse(f"/postular/{token}?p={postulacion.id}", status_code=303)


@router.post("/{token}/responder")
def responder(
    token: str,
    p: int = Form(...),
    opcion_id: int | None = Form(None),
    texto: str = Form(""),
    db: Session = Depends(get_db),
):
    proceso = _proceso_por_token(db, token)
    postulacion = _postulacion_valida(db, proceso, p)
    if postulacion is None:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if postulacion.paso == "cv":
        chatbot.registrar_cv(db, postulacion, texto)
    elif postulacion.paso.startswith("cuestionario:"):
        chatbot.responder_pregunta(db, postulacion, opcion_id=opcion_id, texto=texto)
    return RedirectResponse(f"/postular/{token}?p={postulacion.id}", status_code=303)
