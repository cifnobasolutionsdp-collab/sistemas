"""Dashboard de la organización y gestión de suscripción."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..auth import requiere_login
from ..database import get_db
from ..plantillas import templates

router = APIRouter(prefix="/panel", tags=["panel"])


@router.get("")
def panel(
    request: Request,
    usuario: models.UsuarioPortal = Depends(requiere_login),
    db: Session = Depends(get_db),
):
    org = usuario.organizacion
    suscripcion = org.suscripcion_activa
    otros_usuarios = [u for u in org.usuarios if u.activo]
    return templates.TemplateResponse(
        request,
        "panel.html",
        {
            "usuario": usuario,
            "org": org,
            "suscripcion": suscripcion,
            "otros_usuarios": otros_usuarios,
        },
    )


@router.get("/suscripcion")
def suscripcion_detalle(
    request: Request,
    usuario: models.UsuarioPortal = Depends(requiere_login),
    db: Session = Depends(get_db),
):
    org = usuario.organizacion
    suscripcion = org.suscripcion_activa
    return templates.TemplateResponse(
        request,
        "suscripcion.html",
        {
            "usuario": usuario,
            "org": org,
            "suscripcion": suscripcion,
            "planes": models.PLANES,
        },
    )


@router.post("/suscripcion/cambiar")
def cambiar_plan(
    request: Request,
    db: Session = Depends(get_db),
    usuario: models.UsuarioPortal = Depends(requiere_login),
    nuevo_plan: str = Form(...),
):
    if nuevo_plan not in models.PLANES:
        return RedirectResponse("/panel/suscripcion", status_code=303)
    org = usuario.organizacion
    suscripcion = org.suscripcion_activa
    if suscripcion:
        suscripcion.plan = nuevo_plan
        suscripcion.monto_mensual = models.PLANES[nuevo_plan]["precio_mensual"]
        db.commit()
    return RedirectResponse("/panel/suscripcion", status_code=303)


@router.get("/organizacion")
def organizacion_form(
    request: Request,
    usuario: models.UsuarioPortal = Depends(requiere_login),
):
    return templates.TemplateResponse(
        request,
        "organizacion.html",
        {"usuario": usuario, "org": usuario.organizacion, "guardado": False},
    )


@router.post("/organizacion")
def organizacion_guardar(
    request: Request,
    db: Session = Depends(get_db),
    usuario: models.UsuarioPortal = Depends(requiere_login),
    nombre: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    sitio_web: str = Form(""),
    direccion: str = Form(""),
    num_empleados: str = Form(""),
):
    org = usuario.organizacion
    org.nombre = nombre
    org.telefono = telefono
    org.email = email
    org.sitio_web = sitio_web
    org.direccion = direccion
    org.num_empleados = num_empleados
    db.commit()
    return templates.TemplateResponse(
        request,
        "organizacion.html",
        {"usuario": usuario, "org": org, "guardado": True},
    )
