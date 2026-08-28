"""Configuración compartida de plantillas Jinja2 para el portal."""
from pathlib import Path

from fastapi.templating import Jinja2Templates

from .models import PLANES, TIPOS_ORGANIZACION, ESTADOS_SUSCRIPCION

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def moneda(valor) -> str:
    try:
        return f"${valor:,.0f}"
    except (TypeError, ValueError):
        return "-"


templates.env.filters["moneda"] = moneda
templates.env.globals["PLANES"] = PLANES
templates.env.globals["TIPOS_ORGANIZACION"] = TIPOS_ORGANIZACION
templates.env.globals["ESTADOS_SUSCRIPCION"] = ESTADOS_SUSCRIPCION
