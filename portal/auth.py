"""Autenticación del portal: hashing de contraseñas y gestión de sesiones."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import SesionPortal, UsuarioPortal

COOKIE_NAME = "cifnoba_session"
SESSION_DAYS = 30


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260_000)
    return salt.hex() + ":" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260_000)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False


def crear_sesion(db: Session, usuario: UsuarioPortal) -> str:
    sesion = SesionPortal(
        usuario_id=usuario.id,
        expira_en=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    )
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion.token


def obtener_usuario_actual(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[UsuarioPortal]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    sesion = (
        db.query(SesionPortal)
        .filter(SesionPortal.token == token)
        .first()
    )
    if sesion is None or not sesion.vigente:
        return None
    if not sesion.usuario.activo:
        return None
    return sesion.usuario


def requiere_login(
    request: Request,
    db: Session = Depends(get_db),
) -> UsuarioPortal:
    usuario = obtener_usuario_actual(request, db)
    if usuario is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return usuario


def cerrar_sesion(db: Session, token: str) -> None:
    sesion = db.query(SesionPortal).filter(SesionPortal.token == token).first()
    if sesion:
        db.delete(sesion)
        db.commit()
