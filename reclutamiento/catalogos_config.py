"""Configuración declarativa de los catálogos del sistema de reclutamiento.

Cada catálogo define sus campos una sola vez y el router genérico
(``reclutamiento/routers/catalogos.py``) genera el mantenimiento completo
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
        slug="sucursales",
        titulo="Sucursales",
        modelo=models.Sucursal,
        descripcion="Sucursales de la institución donde se ubican las vacantes.",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("plaza", "Plaza / Ciudad", requerido=False),
            Campo("estado", "Estado", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="areas",
        titulo="Áreas",
        modelo=models.Area,
        descripcion="Áreas o departamentos de la institución (Crédito, Captación, Riesgos…).",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo("descripcion", "Descripción", requerido=False),
        ],
    )
)
_registrar(
    Catalogo(
        slug="canales",
        titulo="Canales de Publicación",
        modelo=models.CanalPublicacion,
        descripcion="Canales donde se difunden las vacantes (portales, redes, correo…).",
        campos=[
            Campo("clave", "Clave"),
            Campo("nombre", "Nombre"),
            Campo(
                "tipo",
                "Tipo",
                "select",
                requerido=True,
                opciones=["portal", "micrositio", "red_social", "correo", "interno"],
            ),
        ],
    )
)


def etiqueta_registro(registro) -> str:
    nombre = getattr(registro, "nombre", None)
    clave = getattr(registro, "clave", None)
    if clave and nombre:
        return f"{clave} — {nombre}"
    return nombre or clave or str(registro.id)
