"""Modelos de datos del módulo de Monitoreo Financiero — Sistema de Evaluación y Monitoreo Financiero."""
from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

TIPOS_ENTIDAD = {"SOCAP": "SOCAP (Cooperativa de Ahorro y Préstamo)", "SOFOM": "SOFOM (Sociedad Financiera de Objeto Múltiple)"}


class Entidad(Base):
    """SOCAP o SOFOM monitoreada."""

    __tablename__ = "mf_entidades"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(10), default="SOCAP")
    nivel: Mapped[str] = mapped_column(String(60), default="")  # nivel de operación / régimen
    # Parámetros IFRS 9 propios (JSON); vacío = parámetros por omisión.
    parametros_ifrs9: Mapped[str] = mapped_column(Text, default="{}")

    estados: Mapped[list["EstadoFinanciero"]] = relationship(
        back_populates="entidad", cascade="all, delete-orphan", order_by="EstadoFinanciero.fecha_corte"
    )

    def params_ifrs9(self) -> dict:
        try:
            return json.loads(self.parametros_ifrs9 or "{}")
        except ValueError:
            return {}


class EstadoFinanciero(Base):
    """Información financiera de una entidad a una fecha de corte, resumida en rubros."""

    __tablename__ = "mf_estados_financieros"
    __table_args__ = (UniqueConstraint("entidad_id", "fecha_corte", name="uq_mf_entidad_fecha"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    entidad_id: Mapped[int] = mapped_column(ForeignKey("mf_entidades.id", ondelete="CASCADE"))
    fecha_corte: Mapped[date] = mapped_column(Date)
    rubros: Mapped[str] = mapped_column(Text, default="{}")
    # Parámetros de mercado del periodo: inflación, tasa de mercado, tasa empresarial.
    inflacion: Mapped[float | None] = mapped_column(Float, nullable=True)
    tasa_mercado: Mapped[float | None] = mapped_column(Float, nullable=True)
    tasa_empresarial: Mapped[float | None] = mapped_column(Float, nullable=True)
    origen: Mapped[str] = mapped_column(String(200), default="")
    actualizado: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    entidad: Mapped[Entidad] = relationship(back_populates="estados")

    def datos(self) -> dict[str, float]:
        try:
            return {k: float(v) for k, v in json.loads(self.rubros or "{}").items()}
        except ValueError:
            return {}

    def fijar(self, datos: dict[str, float]) -> None:
        self.rubros = json.dumps(datos, ensure_ascii=False)


class CargaFinanciera(Base):
    """Bitácora de importaciones de balanzas y estados financieros."""

    __tablename__ = "mf_cargas"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    entidad_id: Mapped[int | None] = mapped_column(ForeignKey("mf_entidades.id", ondelete="SET NULL"), nullable=True)
    fecha_corte: Mapped[date | None] = mapped_column(Date, nullable=True)
    tipo: Mapped[str] = mapped_column(String(30))  # balanza | estados
    archivo: Mapped[str] = mapped_column(String(255))
    renglones: Mapped[int] = mapped_column(Integer, default=0)
    estatus: Mapped[str] = mapped_column(String(20))
    mensaje: Mapped[str] = mapped_column(Text, default="")

    entidad: Mapped[Entidad | None] = relationship()


class ReglaMapeo(Base):
    """Asocia un prefijo de cuenta contable a un rubro.

    ``entidad_id`` nulo = regla general; las reglas de la entidad tienen
    prioridad y, entre ellas, gana el prefijo más largo.
    """

    __tablename__ = "mf_reglas_mapeo"
    __table_args__ = (UniqueConstraint("entidad_id", "prefijo", name="uq_mf_regla"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    entidad_id: Mapped[int | None] = mapped_column(ForeignKey("mf_entidades.id", ondelete="CASCADE"), nullable=True)
    prefijo: Mapped[str] = mapped_column(String(40))
    rubro: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200), default="")

    entidad: Mapped[Entidad | None] = relationship()


class MetaIndicador(Base):
    """Personalización de la meta de un indicador (sobrescribe la meta por omisión)."""

    __tablename__ = "mf_metas"
    __table_args__ = (UniqueConstraint("codigo", "tipo_entidad", name="uq_mf_meta"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10))
    tipo_entidad: Mapped[str] = mapped_column(String(10))
    minimo: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximo: Mapped[float | None] = mapped_column(Float, nullable=True)
