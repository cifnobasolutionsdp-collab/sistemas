"""Configuración compartida de plantillas Jinja2 y filtros de formato."""
from pathlib import Path

from fastapi.templating import Jinja2Templates

from .catalogos_config import CATALOGOS, etiqueta_registro

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def moneda(valor) -> str:
    try:
        return f"${valor:,.2f}"
    except (TypeError, ValueError):
        return "-"


def porcentaje(valor, decimales: int = 2) -> str:
    try:
        return f"{valor:,.{decimales}f}%"
    except (TypeError, ValueError):
        return "-"


def numero(valor) -> str:
    try:
        return f"{valor:,.0f}"
    except (TypeError, ValueError):
        return "-"


templates.env.filters["moneda"] = moneda
templates.env.filters["pct"] = porcentaje
templates.env.filters["num"] = numero
templates.env.globals["CATALOGOS"] = CATALOGOS
templates.env.globals["etiqueta_registro"] = etiqueta_registro
