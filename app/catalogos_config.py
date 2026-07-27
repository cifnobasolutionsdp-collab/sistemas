"""Configuración declarativa de los catálogos del sistema.

Cada catálogo define sus campos una sola vez y el router genérico de
catálogos (``app/routers/catalogos.py``) genera el mantenimiento completo
(alta, consulta, edición y baja) a partir de esta configuración.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import models


@dataclass
class Campo:
    nombre: str
    etiqueta: str
    tipo: str = "text"  # text | number | entero | select
    fk: type | None = None  # modelo relacionado cuando tipo == "select"
    requerido: bool = True
    opciones: list[str] | None = None  # para selects de valores fijos


@dataclass
class Catalogo:
    slug: str
    titulo: str
    modelo: type
    campos: list[Campo] = field(default_factory=list)
    descripcion: str = ""


CATALOGOS: dict[str, Catalogo] = {}


def _registrar(cat: Catalogo) -> None:
    CATALOGOS[cat.slug] = cat


_registrar(
    Catalogo(
        slug="productos",
        titulo="Productos de Crédito",
        modelo=models.ProductoCredito,
        descripcion="Productos de crédito ofrecidos y su tipo de cartera.",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("tipo_cartera_id", "Tipo de Cartera", "select", fk=models.TipoCartera),
            Campo("tasa_referencia", "Tasa de referencia (%)", "number"),
            Campo("descripcion", "Descripción", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="sucursales",
        titulo="Sucursales",
        modelo=models.Sucursal,
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("plaza_id", "Plaza", "select", fk=models.Plaza),
        ],
    )
)
_registrar(
    Catalogo(
        slug="plazas",
        titulo="Plazas",
        modelo=models.Plaza,
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("region_id", "Región", "select", fk=models.Region),
        ],
    )
)
_registrar(
    Catalogo(
        slug="regiones",
        titulo="Regiones",
        modelo=models.Region,
        campos=[Campo("clave", "Clave"), Campo("nombre", "Nombre")],
    )
)
_registrar(
    Catalogo(
        slug="monedas",
        titulo="Monedas",
        modelo=models.Moneda,
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("tipo_cambio", "Tipo de cambio (MXN)", "number"),
        ],
    )
)
_registrar(
    Catalogo(
        slug="tipos-cartera",
        titulo="Tipos de Cartera",
        modelo=models.TipoCartera,
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("descripcion", "Descripción", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="localidades",
        titulo="Localidades",
        modelo=models.Localidad,
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("municipio", "Municipio", requerido=False),
            Campo("estado", "Estado", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="actividades",
        titulo="Actividades",
        modelo=models.Actividad,
        descripcion="Actividades económicas y su sector, para la distribución sectorial de la cartera.",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("sector_economico", "Sector económico"),
        ],
    )
)
_registrar(
    Catalogo(
        slug="garantias",
        titulo="Definición de Garantías",
        modelo=models.Garantia,
        descripcion="Tipos de garantía y su porcentaje de cobertura sobre la exposición.",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("tipo", "Tipo", "select", opciones=["Real", "Personal", "Líquida", "Sin garantía"]),
            Campo("porcentaje_cobertura", "Cobertura (%)", "number"),
            Campo("descripcion", "Descripción", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="calificaciones",
        titulo="Calificaciones de Crédito (PI)",
        modelo=models.CalificacionCredito,
        descripcion=(
            "Grados de riesgo por días de mora con su Probabilidad de "
            "Incumplimiento (PI) y severidad de la pérdida. Parametrizable "
            "conforme a la metodología CNBV vigente."
        ),
        campos=[
            Campo("clave", "Clave"),
            Campo("descripcion", "Descripción", requerido=False),
            Campo("mora_min", "Días de mora desde", "entero"),
            Campo("mora_max", "Días de mora hasta (vacío = sin límite)", "entero", requerido=False),
            Campo("probabilidad_incumplimiento", "Probabilidad de Incumplimiento (%)", "number"),
            Campo("severidad", "Severidad de la pérdida (%)", "number"),
        ],
    )
)
_registrar(
    Catalogo(
        slug="reservas",
        titulo="Reservas Preventivas",
        modelo=models.ReservaPreventiva,
        descripcion="Porcentaje de reserva preventiva por calificación de crédito.",
        campos=[
            Campo("calificacion_id", "Calificación", "select", fk=models.CalificacionCredito),
            Campo("porcentaje_reserva", "Reserva (%)", "number"),
            Campo("descripcion", "Descripción", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="limites",
        titulo="Límites",
        modelo=models.Limite,
        descripcion="Límites de exposición individuales y generales.",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("tipo", "Tipo", "select", opciones=["Individual", "General"]),
            Campo(
                "dimension",
                "Dimensión",
                "select",
                opciones=["Socio", "Producto", "Sucursal", "Sector", "Región", "Cartera"],
            ),
            Campo("valor", "Valor del límite", "number"),
            Campo("unidad", "Unidad", "select", opciones=["MXN", "% Cartera"]),
            Campo("descripcion", "Descripción", requerido=False),
        ],
    )
)


def etiqueta_registro(obj) -> str:
    """Etiqueta legible de un registro de catálogo (para selects y listados)."""
    clave = getattr(obj, "clave", None)
    nombre = getattr(obj, "nombre", None) or getattr(obj, "descripcion", "")
    if clave and nombre:
        return f"{clave} — {nombre}"
    return clave or nombre or f"#{obj.id}"
