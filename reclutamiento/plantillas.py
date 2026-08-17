"""Configuración compartida de plantillas Jinja2 y filtros de formato."""
from pathlib import Path

from fastapi.templating import Jinja2Templates

from .catalogos_config import CATALOGOS, etiqueta_registro
from .models import ESTADOS_POSTULACION, JORNADAS, MODALIDADES, TIPOS_PROCESO

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def moneda(valor) -> str:
    try:
        return f"${valor:,.2f}"
    except (TypeError, ValueError):
        return "-"


def porcentaje(valor, decimales: int = 1) -> str:
    try:
        return f"{valor:,.{decimales}f}%"
    except (TypeError, ValueError):
        return "-"


def numero(valor) -> str:
    try:
        return f"{valor:,.0f}"
    except (TypeError, ValueError):
        return "-"


ETIQUETAS_ESTADO_PROCESO = {
    "borrador": "Borrador",
    "programado": "Programado",
    "publicado": "Publicado",
    "vencido": "Vencido",
    "cerrado": "Cerrado",
}


templates.env.filters["moneda"] = moneda
templates.env.filters["pct"] = porcentaje
templates.env.filters["num"] = numero
templates.env.globals["CATALOGOS"] = CATALOGOS
templates.env.globals["etiqueta_registro"] = etiqueta_registro
templates.env.globals["TIPOS_PROCESO"] = TIPOS_PROCESO
templates.env.globals["JORNADAS"] = JORNADAS
templates.env.globals["MODALIDADES"] = MODALIDADES
templates.env.globals["ESTADOS_POSTULACION"] = ESTADOS_POSTULACION
templates.env.globals["ETIQUETAS_ESTADO_PROCESO"] = ETIQUETAS_ESTADO_PROCESO
