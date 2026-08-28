"""Registro de organizaciones, login y logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..auth import (
    COOKIE_NAME,
    cerrar_sesion,
    crear_sesion,
    hash_password,
    obtener_usuario_actual,
    verify_password,
)
from ..database import get_db
from ..plantillas import templates

router = APIRouter(tags=["auth"])


@router.get("/registro")
def registro_form(request: Request):
    usuario = obtener_usuario_actual(request, next(get_db()))
    if usuario:
        return RedirectResponse("/panel", status_code=303)
    return templates.TemplateResponse(request, "registro.html", {"errores": []})


@router.post("/registro")
def registro_submit(
    request: Request,
    db: Session = Depends(get_db),
    org_nombre: str = Form(...),
    org_rfc: str = Form(...),
    org_tipo: str = Form("socap"),
    org_telefono: str = Form(""),
    org_email: str = Form(""),
    org_num_empleados: str = Form(""),
    usuario_nombre: str = Form(...),
    usuario_email: str = Form(...),
    usuario_password: str = Form(...),
    usuario_password2: str = Form(...),
    plan: str = Form("basico"),
):
    errores = []
    if len(org_rfc) < 12:
        errores.append("El RFC debe tener al menos 12 caracteres.")
    if usuario_password != usuario_password2:
        errores.append("Las contraseñas no coinciden.")
    if len(usuario_password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    if db.query(models.Organizacion).filter(models.Organizacion.rfc == org_rfc.upper()).first():
        errores.append("Ya existe una organización registrada con ese RFC.")
    if db.query(models.UsuarioPortal).filter(models.UsuarioPortal.email == usuario_email).first():
        errores.append("Ya existe una cuenta con ese correo electrónico.")
    if plan not in models.PLANES:
        errores.append("Selecciona un plan válido.")
    if errores:
        return templates.TemplateResponse(request, "registro.html", {"errores": errores})

    org = models.Organizacion(
        nombre=org_nombre,
        rfc=org_rfc.upper().strip(),
        tipo=org_tipo,
        telefono=org_telefono,
        email=org_email,
        num_empleados=org_num_empleados,
    )
    db.add(org)
    db.flush()

    usuario = models.UsuarioPortal(
        organizacion_id=org.id,
        nombre=usuario_nombre,
        email=usuario_email,
        password_hash=hash_password(usuario_password),
        rol="admin",
    )
    db.add(usuario)
    db.flush()

    plan_info = models.PLANES[plan]
    suscripcion = models.Suscripcion(
        organizacion_id=org.id,
        plan=plan,
        estado="prueba",
        monto_mensual=plan_info["precio_mensual"],
        dias_prueba=14,
    )
    db.add(suscripcion)
    db.commit()

    token = crear_sesion(db, usuario)
    response = RedirectResponse("/panel", status_code=303)
    response.set_cookie(COOKIE_NAME, token, max_age=30 * 86400, httponly=True, samesite="lax")
    return response


@router.get("/login")
def login_form(request: Request):
    usuario = obtener_usuario_actual(request, next(get_db()))
    if usuario:
        return RedirectResponse("/panel", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    usuario = db.query(models.UsuarioPortal).filter(models.UsuarioPortal.email == email).first()
    if not usuario or not verify_password(password, usuario.password_hash):
        return templates.TemplateResponse(request, "login.html", {"error": "Correo o contraseña incorrectos."})
    if not usuario.activo:
        return templates.TemplateResponse(request, "login.html", {"error": "Tu cuenta está desactivada."})

    token = crear_sesion(db, usuario)
    response = RedirectResponse("/panel", status_code=303)
    response.set_cookie(COOKIE_NAME, token, max_age=30 * 86400, httponly=True, samesite="lax")
    return response


@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        cerrar_sesion(db, token)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
