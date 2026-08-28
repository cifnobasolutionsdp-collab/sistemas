"""Modelos de datos del portal de suscripciones para organizaciones financieras.

Gestiona el registro de organizaciones (SOCAPS, SOFIPOS, SOFOMES),
usuarios administradores, sesiones de autenticación y suscripciones
a los planes de la plataforma cifnoba.com.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

TIPOS_ORGANIZACION = {
    "socap": "SOCAP (Sociedad Cooperativa de Ahorro y Préstamo)",
    "sofipo": "SOFIPO (Sociedad Financiera Popular)",
    "sofome": "SOFOME (Sociedad Financiera de Objeto Múltiple)",
    "otra": "Otra institución financiera",
}

PLANES = {
    "basico": {
        "nombre": "Básico",
        "precio_mensual": 2499.00,
        "max_vacantes": 3,
        "max_usuarios": 1,
        "incluye_fast_apply": True,
        "incluye_qr": False,
        "incluye_ai": False,
        "soporte": "Correo electrónico",
        "descripcion": "Ideal para instituciones pequeñas que inician su proceso de reclutamiento digital.",
    },
    "profesional": {
        "nombre": "Profesional",
        "precio_mensual": 4999.00,
        "max_vacantes": 10,
        "max_usuarios": 5,
        "incluye_fast_apply": True,
        "incluye_qr": True,
        "incluye_ai": False,
        "soporte": "Correo y teléfono",
        "descripcion": "Para instituciones en crecimiento que necesitan publicar múltiples vacantes.",
    },
    "empresarial": {
        "nombre": "Empresarial",
        "precio_mensual": 9999.00,
        "max_vacantes": 0,
        "max_usuarios": 0,
        "incluye_fast_apply": True,
        "incluye_qr": True,
        "incluye_ai": True,
        "soporte": "Dedicado 24/7",
        "descripcion": "Solución completa para instituciones con alto volumen de contratación.",
    },
}


class Organizacion(Base):
    __tablename__ = "organizaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    rfc: Mapped[str] = mapped_column(String(13), unique=True)
    tipo: Mapped[str] = mapped_column(String(20), default="socap")
    telefono: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    sitio_web: Mapped[str] = mapped_column(String(200), default="")
    direccion: Mapped[str] = mapped_column(Text, default="")
    num_empleados: Mapped[str] = mapped_column(String(30), default="")
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuarios: Mapped[list[UsuarioPortal]] = relationship(
        back_populates="organizacion", cascade="all, delete-orphan"
    )
    suscripciones: Mapped[list[Suscripcion]] = relationship(
        back_populates="organizacion", cascade="all, delete-orphan"
    )

    @property
    def suscripcion_activa(self) -> Suscripcion | None:
        for s in self.suscripciones:
            if s.estado in ("activa", "prueba"):
                return s
        return None

    @property
    def plan_info(self) -> dict | None:
        s = self.suscripcion_activa
        if s and s.plan in PLANES:
            return PLANES[s.plan]
        return None


class UsuarioPortal(Base):
    __tablename__ = "usuarios_portal"
    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"))
    nombre: Mapped[str] = mapped_column(String(180))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    rol: Mapped[str] = mapped_column(String(20), default="admin")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizacion: Mapped[Organizacion] = relationship(back_populates="usuarios")
    sesiones: Mapped[list[SesionPortal]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


def _token_sesion() -> str:
    return secrets.token_urlsafe(32)


class SesionPortal(Base):
    __tablename__ = "sesiones_portal"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios_portal.id"))
    token: Mapped[str] = mapped_column(String(80), unique=True, default=_token_sesion)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expira_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30),
    )

    usuario: Mapped[UsuarioPortal] = relationship(back_populates="sesiones")

    @property
    def vigente(self) -> bool:
        return datetime.utcnow() < self.expira_en


ESTADOS_SUSCRIPCION = {
    "activa": "Activa",
    "prueba": "Periodo de prueba",
    "vencida": "Vencida",
    "cancelada": "Cancelada",
}


class Suscripcion(Base):
    __tablename__ = "suscripciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"))
    plan: Mapped[str] = mapped_column(String(20), default="basico")
    estado: Mapped[str] = mapped_column(String(20), default="prueba")
    monto_mensual: Mapped[float] = mapped_column(Float, default=0.0)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dias_prueba: Mapped[int] = mapped_column(Integer, default=14)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizacion: Mapped[Organizacion] = relationship(back_populates="suscripciones")

    @property
    def plan_info(self) -> dict:
        return PLANES.get(self.plan, PLANES["basico"])
