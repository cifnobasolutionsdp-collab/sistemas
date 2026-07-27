"""Modelos de datos del sistema de Administración de Riesgos de Crédito.

Cubre los catálogos requeridos por la normativa aplicable a SOCAPS y SOFOMES
(Ley de Instituciones de Crédito, LRASCAP y disposiciones de la CNBV), la
cartera de crédito por periodo y los resultados de los procesos de riesgo.
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------
class Region(Base):
    __tablename__ = "regiones"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))


class Plaza(Base):
    __tablename__ = "plazas"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    region_id: Mapped[int] = mapped_column(ForeignKey("regiones.id"))
    region: Mapped[Region] = relationship()


class Sucursal(Base):
    __tablename__ = "sucursales"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    plaza_id: Mapped[int] = mapped_column(ForeignKey("plazas.id"))
    plaza: Mapped[Plaza] = relationship()


class Localidad(Base):
    __tablename__ = "localidades"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    municipio: Mapped[str] = mapped_column(String(120), default="")
    estado: Mapped[str] = mapped_column(String(120), default="")


class Moneda(Base):
    __tablename__ = "monedas"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(10), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo_cambio: Mapped[float] = mapped_column(Float, default=1.0)


class TipoCartera(Base):
    __tablename__ = "tipos_cartera"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(String(250), default="")


class ProductoCredito(Base):
    __tablename__ = "productos_credito"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo_cartera_id: Mapped[int] = mapped_column(ForeignKey("tipos_cartera.id"))
    tasa_referencia: Mapped[float] = mapped_column(Float, default=0.0)
    descripcion: Mapped[str] = mapped_column(String(250), default="")
    tipo_cartera: Mapped[TipoCartera] = relationship()


class Actividad(Base):
    __tablename__ = "actividades"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    sector_economico: Mapped[str] = mapped_column(String(120))


class Garantia(Base):
    __tablename__ = "garantias"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(50))  # Real, Personal, Líquida, Sin garantía
    porcentaje_cobertura: Mapped[float] = mapped_column(Float, default=0.0)
    descripcion: Mapped[str] = mapped_column(String(250), default="")


class CalificacionCredito(Base):
    """Grados de riesgo con su Probabilidad de Incumplimiento (PI) y severidad.

    Los rangos de días de mora y los porcentajes son parametrizables para
    alinearse con la metodología vigente de la CNBV para cada tipo de entidad.
    """

    __tablename__ = "calificaciones_credito"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(10), unique=True)  # A-1, A-2, B, C, D, E
    descripcion: Mapped[str] = mapped_column(String(200), default="")
    mora_min: Mapped[int] = mapped_column(Integer)  # días de mora desde
    mora_max: Mapped[int | None] = mapped_column(Integer, nullable=True)  # hasta (None = sin límite)
    probabilidad_incumplimiento: Mapped[float] = mapped_column(Float)  # % (0-100)
    severidad: Mapped[float] = mapped_column(Float)  # % de pérdida dado incumplimiento (0-100)


class ReservaPreventiva(Base):
    __tablename__ = "reservas_preventivas"
    id: Mapped[int] = mapped_column(primary_key=True)
    calificacion_id: Mapped[int] = mapped_column(ForeignKey("calificaciones_credito.id"), unique=True)
    porcentaje_reserva: Mapped[float] = mapped_column(Float)  # % (0-100)
    descripcion: Mapped[str] = mapped_column(String(200), default="")
    calificacion: Mapped[CalificacionCredito] = relationship()


class Limite(Base):
    """Límites de exposición, individuales y generales."""

    __tablename__ = "limites"
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    tipo: Mapped[str] = mapped_column(String(20))  # Individual | General
    dimension: Mapped[str] = mapped_column(String(30))  # Socio, Producto, Sucursal, Sector, Región, Cartera
    valor: Mapped[float] = mapped_column(Float)
    unidad: Mapped[str] = mapped_column(String(20))  # MXN | % Cartera
    descripcion: Mapped[str] = mapped_column(String(250), default="")


# ---------------------------------------------------------------------------
# Cartera de crédito
# ---------------------------------------------------------------------------
class Prestamo(Base):
    __tablename__ = "prestamos"
    __table_args__ = (UniqueConstraint("periodo", "folio", name="uq_prestamo_periodo_folio"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    periodo: Mapped[str] = mapped_column(String(7), index=True)  # AAAA-MM
    folio: Mapped[str] = mapped_column(String(30), index=True)
    socio: Mapped[str] = mapped_column(String(150))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos_credito.id"))
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"))
    moneda_id: Mapped[int] = mapped_column(ForeignKey("monedas.id"))
    actividad_id: Mapped[int] = mapped_column(ForeignKey("actividades.id"))
    localidad_id: Mapped[int] = mapped_column(ForeignKey("localidades.id"))
    garantia_id: Mapped[int | None] = mapped_column(ForeignKey("garantias.id"), nullable=True)
    monto_original: Mapped[float] = mapped_column(Float)
    saldo_vigente: Mapped[float] = mapped_column(Float, default=0.0)
    saldo_vencido: Mapped[float] = mapped_column(Float, default=0.0)
    dias_mora: Mapped[int] = mapped_column(Integer, default=0)
    plazo_meses: Mapped[int] = mapped_column(Integer)
    tasa_anual: Mapped[float] = mapped_column(Float, default=0.0)
    fecha_otorgamiento: Mapped[date] = mapped_column(Date)
    fecha_vencimiento: Mapped[date] = mapped_column(Date)

    producto: Mapped[ProductoCredito] = relationship()
    sucursal: Mapped[Sucursal] = relationship()
    moneda: Mapped[Moneda] = relationship()
    actividad: Mapped[Actividad] = relationship()
    localidad: Mapped[Localidad] = relationship()
    garantia: Mapped[Garantia | None] = relationship()

    @property
    def exposicion(self) -> float:
        return (self.saldo_vigente or 0.0) + (self.saldo_vencido or 0.0)


class CargaInformacion(Base):
    __tablename__ = "cargas_informacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    periodo: Mapped[str] = mapped_column(String(7))
    archivo: Mapped[str] = mapped_column(String(250))
    registros: Mapped[int] = mapped_column(Integer, default=0)
    rechazados: Mapped[int] = mapped_column(Integer, default=0)
    estatus: Mapped[str] = mapped_column(String(20), default="Exitosa")
    mensaje: Mapped[str] = mapped_column(Text, default="")


class ResultadoRiesgo(Base):
    """Resultados almacenados de los procesos (provisionamiento y VaR)."""

    __tablename__ = "resultados_riesgo"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    periodo: Mapped[str] = mapped_column(String(7), index=True)
    tipo: Mapped[str] = mapped_column(String(30))  # provisionamiento | var
    parametros: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    resultados: Mapped[str] = mapped_column(Text, default="{}")  # JSON
