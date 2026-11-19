"""Configuración compartida de plantillas Jinja2 y filtros de formato."""
from pathlib import Path

from fastapi.templating import Jinja2Templates

from .catalogos_config import CATALOGOS, etiqueta_registro

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def moneda(valor) -> str:
    try:
        return f"-${-valor:,.2f}" if valor < 0 else f"${valor:,.2f}"
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


def pct_decimal(valor, decimales: int = 2) -> str:
    try:
        return f"{valor * 100:,.{decimales}f}%"
    except (TypeError, ValueError):
        return "-"


def valor_indicador(fila) -> str:
    from .monitoreo.exportar import formato_valor

    return formato_valor(fila)


def limite_indicador(valor, formato: str = "pct") -> str:
    if valor is None:
        return "—"
    return f"{valor:,.2f} x" if formato == "veces" else pct_decimal(valor)


templates.env.filters["moneda"] = moneda
templates.env.filters["pctd"] = pct_decimal
templates.env.filters["vind"] = valor_indicador
templates.env.filters["limite"] = limite_indicador
templates.env.filters["pct"] = porcentaje
templates.env.filters["num"] = numero
templates.env.globals["CATALOGOS"] = CATALOGOS
templates.env.globals["etiqueta_registro"] = etiqueta_registro
