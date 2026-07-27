"""Consultas y agregaciones sobre la cartera de crédito.

Todas las consultas reportan Saldo Vigente y Saldo Vencido.
"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from . import models

DIMENSIONES = {
    "producto": "Producto de Crédito",
    "sucursal": "Sucursal",
    "plaza": "Plaza",
    "sector": "Sector Económico",
    "region": "Región",
}

BUCKETS_PLAZO = [
    ("Hasta 6 meses", 0, 6),
    ("7 a 12 meses", 7, 12),
    ("13 a 24 meses", 13, 24),
    ("25 a 36 meses", 25, 36),
    ("Más de 36 meses", 37, None),
]

BUCKETS_MONTO = [
    ("Hasta $10,000", 0, 10_000),
    ("$10,001 a $50,000", 10_001, 50_000),
    ("$50,001 a $100,000", 50_001, 100_000),
    ("$100,001 a $500,000", 100_001, 500_000),
    ("Más de $500,000", 500_001, None),
]


def periodos_disponibles(db: Session) -> list[str]:
    filas = db.query(models.Prestamo.periodo).distinct().order_by(models.Prestamo.periodo).all()
    return [f[0] for f in filas]


def periodo_actual(db: Session, solicitado: str | None = None) -> str | None:
    periodos = periodos_disponibles(db)
    if solicitado and solicitado in periodos:
        return solicitado
    return periodos[-1] if periodos else None


def _prestamos(db: Session, periodo: str) -> list[models.Prestamo]:
    return db.query(models.Prestamo).filter(models.Prestamo.periodo == periodo).all()


def _resumen(filas: list[dict]) -> dict:
    total = {
        "creditos": sum(f["creditos"] for f in filas),
        "saldo_vigente": sum(f["saldo_vigente"] for f in filas),
        "saldo_vencido": sum(f["saldo_vencido"] for f in filas),
    }
    total["total"] = total["saldo_vigente"] + total["saldo_vencido"]
    cartera = total["total"] or 1.0
    for f in filas:
        f["total"] = f["saldo_vigente"] + f["saldo_vencido"]
        f["participacion"] = f["total"] / cartera * 100.0
        f["imor"] = (f["saldo_vencido"] / f["total"] * 100.0) if f["total"] else 0.0
    total["imor"] = (total["saldo_vencido"] / total["total"] * 100.0) if total["total"] else 0.0
    return total


def _agrupar(prestamos, llave) -> list[dict]:
    grupos: dict[str, dict] = defaultdict(
        lambda: {"creditos": 0, "saldo_vigente": 0.0, "saldo_vencido": 0.0, "monto_original": 0.0}
    )
    for p in prestamos:
        g = grupos[llave(p)]
        g["creditos"] += 1
        g["saldo_vigente"] += p.saldo_vigente or 0.0
        g["saldo_vencido"] += p.saldo_vencido or 0.0
        g["monto_original"] += p.monto_original or 0.0
    filas = [{"grupo": nombre, **datos} for nombre, datos in grupos.items()]
    filas.sort(key=lambda f: f["saldo_vigente"] + f["saldo_vencido"], reverse=True)
    return filas


def _por_buckets(prestamos, buckets, valor) -> list[dict]:
    filas = []
    for etiqueta, minimo, maximo in buckets:
        seleccion = [
            p for p in prestamos
            if valor(p) >= minimo and (maximo is None or valor(p) <= maximo)
        ]
        filas.append(
            {
                "grupo": etiqueta,
                "creditos": len(seleccion),
                "saldo_vigente": sum(p.saldo_vigente or 0.0 for p in seleccion),
                "saldo_vencido": sum(p.saldo_vencido or 0.0 for p in seleccion),
                "monto_original": sum(p.monto_original or 0.0 for p in seleccion),
            }
        )
    return filas


def prestamos_por_plazo(db: Session, periodo: str) -> tuple[list[dict], dict]:
    filas = _por_buckets(_prestamos(db, periodo), BUCKETS_PLAZO, lambda p: p.plazo_meses or 0)
    return filas, _resumen(filas)


def prestamos_por_monto(db: Session, periodo: str) -> tuple[list[dict], dict]:
    filas = _por_buckets(_prestamos(db, periodo), BUCKETS_MONTO, lambda p: p.monto_original or 0.0)
    return filas, _resumen(filas)


def distribucion(db: Session, periodo: str, dimension: str) -> tuple[list[dict], dict]:
    llaves = {
        "producto": lambda p: p.producto.nombre,
        "sucursal": lambda p: p.sucursal.nombre,
        "plaza": lambda p: p.sucursal.plaza.nombre,
        "sector": lambda p: p.actividad.sector_economico,
        "region": lambda p: p.sucursal.plaza.region.nombre,
    }
    filas = _agrupar(_prestamos(db, periodo), llaves[dimension])
    return filas, _resumen(filas)


def evolucion_historica(db: Session) -> list[dict]:
    filas = []
    for periodo in periodos_disponibles(db):
        prestamos = _prestamos(db, periodo)
        vigente = sum(p.saldo_vigente or 0.0 for p in prestamos)
        vencido = sum(p.saldo_vencido or 0.0 for p in prestamos)
        total = vigente + vencido
        filas.append(
            {
                "periodo": periodo,
                "creditos": len(prestamos),
                "saldo_vigente": vigente,
                "saldo_vencido": vencido,
                "total": total,
                "imor": (vencido / total * 100.0) if total else 0.0,
            }
        )
    return filas


def seguimiento_limites(db: Session, periodo: str) -> list[dict]:
    """Compara cada límite del catálogo contra la posición actual de la cartera."""
    prestamos = _prestamos(db, periodo)
    cartera_total = sum(p.exposicion for p in prestamos)

    por_socio = _agrupar(prestamos, lambda p: p.socio)
    agrupaciones = {
        "Socio": por_socio,
        "Producto": _agrupar(prestamos, lambda p: p.producto.nombre),
        "Sucursal": _agrupar(prestamos, lambda p: p.sucursal.nombre),
        "Sector": _agrupar(prestamos, lambda p: p.actividad.sector_economico),
        "Región": _agrupar(prestamos, lambda p: p.sucursal.plaza.region.nombre),
    }

    resultados = []
    for limite in db.query(models.Limite).order_by(models.Limite.tipo, models.Limite.clave).all():
        if limite.dimension == "Cartera":
            actual = cartera_total
            detalle = "Cartera total"
        else:
            filas = agrupaciones.get(limite.dimension, [])
            if filas:
                mayor = max(filas, key=lambda f: f["saldo_vigente"] + f["saldo_vencido"])
                actual = mayor["saldo_vigente"] + mayor["saldo_vencido"]
                detalle = f"Mayor exposición: {mayor['grupo']}"
            else:
                actual, detalle = 0.0, "Sin datos"

        if limite.unidad == "% Cartera":
            actual_medido = (actual / cartera_total * 100.0) if cartera_total else 0.0
        else:
            actual_medido = actual

        uso = (actual_medido / limite.valor * 100.0) if limite.valor else 0.0
        resultados.append(
            {
                "limite": limite,
                "actual": actual_medido,
                "uso": uso,
                "detalle": detalle,
                "cumple": actual_medido <= limite.valor,
            }
        )
    return resultados
