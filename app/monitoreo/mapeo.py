"""Mapeo de cuentas contables (balanza de comprobación) a rubros.

Las reglas por omisión siguen un catálogo de cuentas de referencia de cuatro
dígitos (1 Activo, 2 Pasivo, 3 Capital, 4 Ingresos, 5 Gastos), alineado a la
estructura de los criterios contables de la CNBV para SOCAPS y SOFOMES con
cartera clasificada en etapas 1, 2 y 3 (enfoque de pérdida esperada de
IFRS 9 / NIF C-16). **Cada entidad debe revisar y ajustar las reglas a su
propio catálogo** desde *Evaluación y Monitoreo Financiero → Mapeo de cuentas*, o bien
incluir la columna ``rubro`` en la balanza para asignar cada cuenta de forma
explícita.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from .modelos import ReglaMapeo

REGLAS_POR_OMISION: list[tuple[str, str, str]] = [
    # prefijo, rubro, descripción
    ("1101", "caja", "Caja"),
    ("1102", "bancos", "Bancos"),
    ("1103", "bancos", "Otras disponibilidades"),
    ("1201", "inversiones_cp", "Inversiones en valores de corto plazo"),
    ("1202", "inversiones_lp", "Inversiones en valores de largo plazo"),
    ("1203", "inversiones_lp", "Inversiones conservadas a vencimiento"),
    ("1301", "cartera_etapa1", "Cartera de crédito con riesgo de crédito etapa 1"),
    ("1302", "cartera_etapa2", "Cartera de crédito con riesgo de crédito etapa 2"),
    ("1303", "cartera_etapa3", "Cartera de crédito con riesgo de crédito etapa 3"),
    ("1304", "estimaciones", "Estimación preventiva para riesgos crediticios"),
    ("14", "cuentas_por_cobrar", "Otras cuentas por cobrar"),
    ("15", "bienes_adjudicados", "Bienes adjudicados"),
    ("16", "activo_fijo", "Propiedades, mobiliario y equipo"),
    ("17", "inversiones_permanentes", "Inversiones permanentes"),
    ("18", "otros_activos", "Otros activos"),
    ("19", "otros_activos", "Otros activos"),
    ("2101", "depositos_vista", "Depósitos de exigibilidad inmediata"),
    ("2102", "depositos_plazo", "Depósitos a plazo"),
    ("22", "prestamos_bancarios", "Préstamos bancarios y de otros organismos"),
    ("23", "cuentas_por_pagar", "Otras cuentas por pagar"),
    ("24", "otros_pasivos", "Créditos diferidos y cobros anticipados"),
    ("25", "otros_pasivos", "Otros pasivos"),
    ("31", "capital_social", "Capital social"),
    ("3201", "reservas_capital", "Fondo de reserva"),
    ("3202", "resultados_anteriores", "Resultado de ejercicios anteriores"),
    ("3203", "resultado_ejercicio", "Resultado neto del ejercicio"),
    ("3204", "reservas_capital", "Otras reservas / resultado por valuación"),
    ("4101", "ing_intereses_cartera", "Intereses de cartera de crédito"),
    ("4102", "ing_disponibilidades", "Intereses de disponibilidades e inversiones de corto plazo"),
    ("4103", "ing_inversiones_lp", "Intereses de inversiones de largo plazo"),
    ("4104", "ing_inversiones_permanentes", "Ingresos por inversiones permanentes"),
    ("42", "comisiones_cobradas", "Comisiones y tarifas cobradas"),
    ("43", "otros_ingresos", "Otros ingresos de la operación"),
    ("44", "otros_ingresos", "Recuperaciones y otros ingresos"),
    ("5101", "int_depositos", "Intereses por depósitos"),
    ("5102", "int_prestamos_bancarios", "Intereses por préstamos bancarios"),
    ("5103", "int_aportaciones", "Rendimientos sobre aportaciones"),
    ("52", "comisiones_pagadas", "Comisiones y tarifas pagadas"),
    ("53", "provisiones", "Estimación preventiva para riesgos crediticios"),
    ("54", "gastos_administracion", "Gastos de administración y promoción"),
    ("55", "otros_gastos", "Otros gastos de la operación"),
    ("56", "impuestos", "Impuestos y PTU"),
]


def normalizar_cuenta(cuenta: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(cuenta or "")).strip()


def sembrar_reglas(db: Session) -> None:
    """Crea las reglas generales por omisión si aún no existen."""
    if db.query(ReglaMapeo).filter(ReglaMapeo.entidad_id.is_(None)).count():
        return
    for prefijo, rubro, desc in REGLAS_POR_OMISION:
        db.add(ReglaMapeo(entidad_id=None, prefijo=prefijo, rubro=rubro, descripcion=desc))
    db.commit()


class Mapeador:
    """Resuelve el rubro de una cuenta (prefijo más largo; primero las reglas de la entidad)."""

    def __init__(self, db: Session, entidad_id: int | None):
        sembrar_reglas(db)
        reglas = db.query(ReglaMapeo).filter(
            (ReglaMapeo.entidad_id.is_(None)) | (ReglaMapeo.entidad_id == entidad_id)
        ).all()
        self.propias = sorted(
            [(normalizar_cuenta(r.prefijo), r.rubro) for r in reglas if r.entidad_id is not None],
            key=lambda x: -len(x[0]),
        )
        self.generales = sorted(
            [(normalizar_cuenta(r.prefijo), r.rubro) for r in reglas if r.entidad_id is None],
            key=lambda x: -len(x[0]),
        )

    def rubro(self, cuenta: str) -> str | None:
        c = normalizar_cuenta(cuenta)
        for lista in (self.propias, self.generales):
            for prefijo, rubro in lista:
                if prefijo and c.startswith(prefijo):
                    return rubro
        return None
