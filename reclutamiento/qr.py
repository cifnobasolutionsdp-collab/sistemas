"""Generación de códigos QR en SVG para los pósters de difusión.

Utiliza ``segno`` (implementación pura de Python, sin dependencias) para
producir un SVG incrustable en la página del póster del proceso.
"""
from __future__ import annotations

import io

import segno


def qr_svg(contenido: str, escala: int = 6) -> str:
    """Devuelve el código QR de ``contenido`` como cadena SVG."""
    buffer = io.BytesIO()
    segno.make(contenido, error="m").save(
        buffer, kind="svg", scale=escala, dark="#14406e", xmldecl=False
    )
    return buffer.getvalue().decode("utf-8")
