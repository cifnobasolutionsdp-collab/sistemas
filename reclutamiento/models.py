"""Modelos de datos del sistema de Reclutamiento y Selección.

Orientado a instituciones financieras mexicanas (SOCAPS, SOFIPOS y SOFOMES):
procesos de vacantes con postulación conversacional exprés («Fast Apply»),
preguntas de filtro con ponderación y opciones excluyentes, mensajes de
chatbot configurables, publicación multicanal y gestión de candidatos con
CV autogenerado y nivel de adecuación.
"""
from __future__ import annotations

import secrets
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Tipos de proceso (equivalentes a las alternativas de creación del producto)
TIPOS_PROCESO = {
    "fast_apply": "Proceso Fast Apply",
    "estandar": "Proceso Estándar",
}

JORNADAS = ["Jornada Completa", "Medio Tiempo", "Por Horas", "Fines de Semana"]
MODALIDADES = ["Presencial", "Híbrido", "Remoto"]

ESTADOS_POSTULACION = {
    "en_curso": "En conversación",
    "postulado": "Postulado",
    "preseleccionado": "Preseleccionado",
    "descartado": "Descartado",
    "contratado": "Contratado",
}


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------
class Sucursal(Base):
    __tablename__ = "sucursales"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    plaza: Mapped[str] = mapped_column(String(120), default="")
    estado: Mapped[str] = mapped_column(String(120), default="")


class Area(Base):
    __tablename__ = "areas"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(String(250), default="")


class CanalPublicacion(Base):
    __tablename__ = "canales_publicacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    # portal | micrositio | red_social | correo | interno
    tipo: Mapped[str] = mapped_column(String(30), default="portal")


# ---------------------------------------------------------------------------
# Procesos de reclutamiento (vacantes)
# ---------------------------------------------------------------------------
def _nuevo_token() -> str:
    return secrets.token_urlsafe(9)


class Proceso(Base):
    __tablename__ = "procesos"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), default="fast_apply")
    posicion: Mapped[str] = mapped_column(String(180))
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), nullable=True)
    jornada: Mapped[str] = mapped_column(String(60), default="Jornada Completa")
    modalidad: Mapped[str] = mapped_column(String(40), default="Presencial")
    descripcion: Mapped[str] = mapped_column(Text, default="")
    vacantes: Mapped[int] = mapped_column(Integer, default=1)
    salario_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salario_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Publicación y desactivación automáticas
    fecha_publicacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    cerrado: Mapped[bool] = mapped_column(Boolean, default=False)

    # Mensajes configurables del chatbot (máx. 300 caracteres cada uno)
    solicitar_cv: Mapped[bool] = mapped_column(Boolean, default=True)
    msg_bienvenida: Mapped[str] = mapped_column(String(300), default="")
    msg_solicitud_cv: Mapped[str] = mapped_column(String(300), default="")
    msg_pre_cuestionario: Mapped[str] = mapped_column(String(300), default="")
    msg_despedida: Mapped[str] = mapped_column(String(300), default="")

    token: Mapped[str] = mapped_column(String(40), unique=True, default=_nuevo_token)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    area: Mapped[Area | None] = relationship()
    sucursal: Mapped[Sucursal | None] = relationship()
    preguntas: Mapped[list[PreguntaFiltro]] = relationship(
        back_populates="proceso", cascade="all, delete-orphan", order_by="PreguntaFiltro.orden"
    )
    canales: Mapped[list[CanalProceso]] = relationship(
        back_populates="proceso", cascade="all, delete-orphan"
    )
    postulaciones: Mapped[list[Postulacion]] = relationship(
        back_populates="proceso", cascade="all, delete-orphan"
    )

    @property
    def estado(self) -> str:
        """Estado calculado con base en las fechas de publicación."""
        if self.cerrado:
            return "cerrado"
        hoy = date.today()
        if self.fecha_publicacion is None:
            return "borrador"
        if self.fecha_publicacion > hoy:
            return "programado"
        if self.fecha_fin is not None and self.fecha_fin < hoy:
            return "vencido"
        return "publicado"

    @property
    def recibe_postulaciones(self) -> bool:
        return self.estado == "publicado"


class PreguntaFiltro(Base):
    """Pregunta de filtro («killer question») del cuestionario del chatbot."""

    __tablename__ = "preguntas_filtro"
    id: Mapped[int] = mapped_column(primary_key=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"))
    orden: Mapped[int] = mapped_column(Integer, default=1)
    texto: Mapped[str] = mapped_column(String(300))
    tipo: Mapped[str] = mapped_column(String(10), default="cerrada")  # cerrada | abierta

    proceso: Mapped[Proceso] = relationship(back_populates="preguntas")
    opciones: Mapped[list[OpcionRespuesta]] = relationship(
        back_populates="pregunta", cascade="all, delete-orphan", order_by="OpcionRespuesta.id"
    )

    @property
    def peso_maximo(self) -> float:
        pesos = [o.peso for o in self.opciones if not o.excluyente]
        return max(pesos) if pesos else 0.0


class OpcionRespuesta(Base):
    """Opción de respuesta de una pregunta cerrada, con peso o excluyente."""

    __tablename__ = "opciones_respuesta"
    id: Mapped[int] = mapped_column(primary_key=True)
    pregunta_id: Mapped[int] = mapped_column(ForeignKey("preguntas_filtro.id"))
    texto: Mapped[str] = mapped_column(String(120))
    peso: Mapped[float] = mapped_column(Float, default=0.0)
    excluyente: Mapped[bool] = mapped_column(Boolean, default=False)

    pregunta: Mapped[PreguntaFiltro] = relationship(back_populates="opciones")


class CanalProceso(Base):
    """Canal en el que se difunde un proceso."""

    __tablename__ = "canales_proceso"
    id: Mapped[int] = mapped_column(primary_key=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"))
    canal_id: Mapped[int] = mapped_column(ForeignKey("canales_publicacion.id"))

    proceso: Mapped[Proceso] = relationship(back_populates="canales")
    canal: Mapped[CanalPublicacion] = relationship()


# ---------------------------------------------------------------------------
# Postulaciones (conversación Fast Apply y candidatos)
# ---------------------------------------------------------------------------
class Postulacion(Base):
    __tablename__ = "postulaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"))
    nombre: Mapped[str] = mapped_column(String(180))
    telefono: Mapped[str] = mapped_column(String(30), default="")
    correo: Mapped[str] = mapped_column(String(180), default="")
    resumen_cv: Mapped[str] = mapped_column(Text, default="")

    # paso: cv | cuestionario:<índice> | fin
    paso: Mapped[str] = mapped_column(String(30), default="cv")
    estado: Mapped[str] = mapped_column(String(20), default="en_curso")
    puntaje: Mapped[float] = mapped_column(Float, default=0.0)
    adecuacion: Mapped[float | None] = mapped_column(Float, nullable=True)
    iniciada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    proceso: Mapped[Proceso] = relationship(back_populates="postulaciones")
    respuestas: Mapped[list[RespuestaCandidato]] = relationship(
        back_populates="postulacion", cascade="all, delete-orphan"
    )
    mensajes: Mapped[list[MensajeChat]] = relationship(
        back_populates="postulacion", cascade="all, delete-orphan", order_by="MensajeChat.id"
    )

    @property
    def duracion_minutos(self) -> float | None:
        if self.completada_en is None:
            return None
        return (self.completada_en - self.iniciada_en).total_seconds() / 60.0


class RespuestaCandidato(Base):
    __tablename__ = "respuestas_candidato"
    id: Mapped[int] = mapped_column(primary_key=True)
    postulacion_id: Mapped[int] = mapped_column(ForeignKey("postulaciones.id"))
    pregunta_id: Mapped[int] = mapped_column(ForeignKey("preguntas_filtro.id"))
    opcion_id: Mapped[int | None] = mapped_column(ForeignKey("opciones_respuesta.id"), nullable=True)
    texto: Mapped[str] = mapped_column(Text, default="")

    postulacion: Mapped[Postulacion] = relationship(back_populates="respuestas")
    pregunta: Mapped[PreguntaFiltro] = relationship()
    opcion: Mapped[OpcionRespuesta | None] = relationship()


class MensajeChat(Base):
    """Transcripción de la conversación del chatbot con el candidato."""

    __tablename__ = "mensajes_chat"
    id: Mapped[int] = mapped_column(primary_key=True)
    postulacion_id: Mapped[int] = mapped_column(ForeignKey("postulaciones.id"))
    emisor: Mapped[str] = mapped_column(String(10))  # bot | candidato
    texto: Mapped[str] = mapped_column(Text)
    enviado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    postulacion: Mapped[Postulacion] = relationship(back_populates="mensajes")
