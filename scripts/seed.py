"""Siembra catálogos y una cartera de demostración.

Uso:  python scripts/seed.py [--sin-cartera]

Los porcentajes de reservas y probabilidades de incumplimiento sembrados son
valores de referencia parametrizables; deben ajustarse a la disposición CNBV
vigente aplicable a la entidad.
"""
from __future__ import annotations

import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402

rng = random.Random(2026)

PERIODOS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]


def sembrar_catalogos(db) -> None:
    regiones = [
        models.Region(clave="NORTE", nombre="Norte"),
        models.Region(clave="CENTRO", nombre="Centro"),
        models.Region(clave="SUR", nombre="Sur"),
    ]
    db.add_all(regiones)
    db.flush()

    plazas = [
        models.Plaza(clave="MTY", nombre="Monterrey", region_id=regiones[0].id),
        models.Plaza(clave="SALT", nombre="Saltillo", region_id=regiones[0].id),
        models.Plaza(clave="CDMX", nombre="Ciudad de México", region_id=regiones[1].id),
        models.Plaza(clave="QRO", nombre="Querétaro", region_id=regiones[1].id),
        models.Plaza(clave="OAX", nombre="Oaxaca", region_id=regiones[2].id),
        models.Plaza(clave="TUX", nombre="Tuxtla Gutiérrez", region_id=regiones[2].id),
    ]
    db.add_all(plazas)
    db.flush()

    sucursales = []
    for plaza in plazas:
        for i in (1, 2):
            sucursales.append(
                models.Sucursal(
                    clave=f"{plaza.clave}{i:02d}",
                    nombre=f"Sucursal {plaza.nombre} {i}",
                    plaza_id=plaza.id,
                )
            )
    db.add_all(sucursales)

    db.add_all(
        [
            models.Localidad(clave="LOC01", nombre="Centro", municipio="Monterrey", estado="Nuevo León"),
            models.Localidad(clave="LOC02", nombre="Ramos Arizpe", municipio="Ramos Arizpe", estado="Coahuila"),
            models.Localidad(clave="LOC03", nombre="Iztapalapa", municipio="Iztapalapa", estado="CDMX"),
            models.Localidad(clave="LOC04", nombre="El Marqués", municipio="El Marqués", estado="Querétaro"),
            models.Localidad(clave="LOC05", nombre="Xoxocotlán", municipio="Santa Cruz Xoxocotlán", estado="Oaxaca"),
            models.Localidad(clave="LOC06", nombre="Terán", municipio="Tuxtla Gutiérrez", estado="Chiapas"),
        ]
    )

    db.add_all(
        [
            models.Moneda(clave="MXN", nombre="Peso mexicano", tipo_cambio=1.0),
            models.Moneda(clave="UDI", nombre="Unidad de Inversión", tipo_cambio=8.35),
            models.Moneda(clave="USD", nombre="Dólar estadounidense", tipo_cambio=17.10),
        ]
    )

    tipos = [
        models.TipoCartera(clave="CONS", nombre="Consumo", descripcion="Créditos de consumo"),
        models.TipoCartera(clave="COM", nombre="Comercial", descripcion="Créditos comerciales y productivos"),
        models.TipoCartera(clave="VIV", nombre="Vivienda", descripcion="Créditos a la vivienda"),
    ]
    db.add_all(tipos)
    db.flush()

    db.add_all(
        [
            models.ProductoCredito(clave="PNOM", nombre="Préstamo de Nómina", tipo_cartera_id=tipos[0].id, tasa_referencia=24.0),
            models.ProductoCredito(clave="PPER", nombre="Préstamo Personal", tipo_cartera_id=tipos[0].id, tasa_referencia=28.0),
            models.ProductoCredito(clave="PAUT", nombre="Crédito Automotriz", tipo_cartera_id=tipos[0].id, tasa_referencia=16.5),
            models.ProductoCredito(clave="PCOM", nombre="Crédito Comercial PyME", tipo_cartera_id=tipos[1].id, tasa_referencia=18.0),
            models.ProductoCredito(clave="PAGR", nombre="Crédito Agropecuario", tipo_cartera_id=tipos[1].id, tasa_referencia=14.0),
            models.ProductoCredito(clave="PVIV", nombre="Crédito de Vivienda", tipo_cartera_id=tipos[2].id, tasa_referencia=11.5),
        ]
    )

    db.add_all(
        [
            models.Actividad(clave="ACT01", nombre="Empleado asalariado", sector_economico="Servicios"),
            models.Actividad(clave="ACT02", nombre="Comercio al por menor", sector_economico="Comercio"),
            models.Actividad(clave="ACT03", nombre="Agricultura y ganadería", sector_economico="Agropecuario"),
            models.Actividad(clave="ACT04", nombre="Manufactura ligera", sector_economico="Industria"),
            models.Actividad(clave="ACT05", nombre="Transporte de carga", sector_economico="Transporte"),
            models.Actividad(clave="ACT06", nombre="Construcción", sector_economico="Construcción"),
        ]
    )

    db.add_all(
        [
            models.Garantia(clave="GHIP", nombre="Garantía hipotecaria", tipo="Real", porcentaje_cobertura=70.0),
            models.Garantia(clave="GPRE", nombre="Garantía prendaria", tipo="Real", porcentaje_cobertura=50.0),
            models.Garantia(clave="GLIQ", nombre="Garantía líquida (ahorro)", tipo="Líquida", porcentaje_cobertura=90.0),
            models.Garantia(clave="GAVA", nombre="Aval / obligado solidario", tipo="Personal", porcentaje_cobertura=20.0),
            models.Garantia(clave="GSIN", nombre="Sin garantía", tipo="Sin garantía", porcentaje_cobertura=0.0),
        ]
    )

    calificaciones = [
        models.CalificacionCredito(clave="A", descripcion="Riesgo mínimo", mora_min=0, mora_max=0, probabilidad_incumplimiento=1.0, severidad=55.0),
        models.CalificacionCredito(clave="B", descripcion="Riesgo bajo", mora_min=1, mora_max=30, probabilidad_incumplimiento=8.0, severidad=60.0),
        models.CalificacionCredito(clave="C", descripcion="Riesgo medio", mora_min=31, mora_max=60, probabilidad_incumplimiento=30.0, severidad=65.0),
        models.CalificacionCredito(clave="D", descripcion="Riesgo alto", mora_min=61, mora_max=90, probabilidad_incumplimiento=60.0, severidad=70.0),
        models.CalificacionCredito(clave="E", descripcion="Irrecuperable", mora_min=91, mora_max=None, probabilidad_incumplimiento=95.0, severidad=80.0),
    ]
    db.add_all(calificaciones)
    db.flush()

    porcentajes_reserva = {"A": 0.5, "B": 10.0, "C": 45.0, "D": 65.0, "E": 100.0}
    db.add_all(
        [
            models.ReservaPreventiva(
                calificacion_id=c.id,
                porcentaje_reserva=porcentajes_reserva[c.clave],
                descripcion=f"Reserva para grado {c.clave}",
            )
            for c in calificaciones
        ]
    )

    db.add_all(
        [
            models.Limite(clave="LIM-IND", nombre="Exposición máxima por socio", tipo="Individual", dimension="Socio", valor=1_500_000.0, unidad="MXN", descripcion="Límite de riesgo común por acreditado"),
            models.Limite(clave="LIM-CAR", nombre="Cartera total máxima", tipo="General", dimension="Cartera", valor=250_000_000.0, unidad="MXN"),
            models.Limite(clave="LIM-SEC", nombre="Concentración máxima por sector", tipo="General", dimension="Sector", valor=35.0, unidad="% Cartera"),
            models.Limite(clave="LIM-PRO", nombre="Concentración máxima por producto", tipo="General", dimension="Producto", valor=40.0, unidad="% Cartera"),
            models.Limite(clave="LIM-REG", nombre="Concentración máxima por región", tipo="General", dimension="Región", valor=50.0, unidad="% Cartera"),
        ]
    )
    db.commit()


NOMBRES = [
    "María", "José", "Guadalupe", "Juan", "Verónica", "Luis", "Carmen", "Miguel",
    "Rosa", "Francisco", "Alejandra", "Antonio", "Leticia", "Pedro", "Gabriela",
    "Jorge", "Patricia", "Ricardo", "Elena", "Raúl",
]
APELLIDOS = [
    "Hernández", "García", "Martínez", "López", "González", "Pérez", "Rodríguez",
    "Sánchez", "Ramírez", "Cruz", "Flores", "Gómez", "Morales", "Vázquez", "Reyes",
]


def sembrar_cartera(db) -> None:
    productos = db.query(models.ProductoCredito).all()
    sucursales = db.query(models.Sucursal).all()
    moneda_mxn = db.query(models.Moneda).filter_by(clave="MXN").one()
    actividades = db.query(models.Actividad).all()
    localidades = db.query(models.Localidad).all()
    garantias = db.query(models.Garantia).all()

    rangos_monto = {
        "PNOM": (8_000, 120_000), "PPER": (5_000, 80_000), "PAUT": (80_000, 450_000),
        "PCOM": (50_000, 1_200_000), "PAGR": (30_000, 600_000), "PVIV": (250_000, 1_800_000),
    }

    # 320 acreditados base; cada periodo la cartera evoluciona (amortiza y rota)
    socios = [
        f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"
        for _ in range(320)
    ]

    creditos_base = []
    for i in range(420):
        producto = rng.choice(productos)
        minimo, maximo = rangos_monto[producto.clave]
        monto = round(rng.uniform(minimo, maximo), -2)
        plazo = rng.choice([6, 12, 18, 24, 36, 48, 60])
        anio = rng.choice([2024, 2025])
        otorgado = date(anio, rng.randint(1, 12), rng.randint(1, 28))
        creditos_base.append(
            {
                "folio": f"CR{i + 1:05d}",
                "socio": rng.choice(socios),
                "producto": producto,
                "sucursal": rng.choice(sucursales),
                "actividad": rng.choice(actividades),
                "localidad": rng.choice(localidades),
                "garantia": rng.choice(garantias),
                "monto": monto,
                "plazo": plazo,
                "tasa": round(producto.tasa_referencia + rng.uniform(-2, 4), 2),
                "otorgado": otorgado,
                "mora": 0,
            }
        )

    for indice_periodo, periodo in enumerate(PERIODOS):
        for c in creditos_base:
            # Evolución de mora: la mayoría al corriente, algunos se deterioran
            azar = rng.random()
            if c["mora"] > 0:
                c["mora"] = c["mora"] + 30 if azar < 0.55 else 0
            elif azar < 0.06:
                c["mora"] = rng.choice([15, 30, 45])

            factor_amortizacion = max(0.15, 1.0 - 0.035 * (indice_periodo + rng.uniform(0, 3)))
            saldo = c["monto"] * factor_amortizacion
            if c["mora"] == 0:
                vigente, vencido = saldo, 0.0
            else:
                proporcion_vencida = min(0.15 + c["mora"] / 300.0, 0.9)
                vencido = saldo * proporcion_vencida
                vigente = saldo - vencido

            anio_v = c["otorgado"].year + c["plazo"] // 12
            mes_v = c["otorgado"].month + c["plazo"] % 12
            if mes_v > 12:
                anio_v, mes_v = anio_v + 1, mes_v - 12
            db.add(
                models.Prestamo(
                    periodo=periodo,
                    folio=c["folio"],
                    socio=c["socio"],
                    producto_id=c["producto"].id,
                    sucursal_id=c["sucursal"].id,
                    moneda_id=moneda_mxn.id,
                    actividad_id=c["actividad"].id,
                    localidad_id=c["localidad"].id,
                    garantia_id=c["garantia"].id,
                    monto_original=c["monto"],
                    saldo_vigente=round(vigente, 2),
                    saldo_vencido=round(vencido, 2),
                    dias_mora=c["mora"],
                    plazo_meses=c["plazo"],
                    tasa_anual=c["tasa"],
                    fecha_otorgamiento=c["otorgado"],
                    fecha_vencimiento=date(anio_v, mes_v, min(c["otorgado"].day, 28)),
                )
            )
        db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Region).count() > 0:
            print("La base ya contiene catálogos; no se vuelve a sembrar.")
            return
        sembrar_catalogos(db)
        print("Catálogos sembrados.")
        if "--sin-cartera" not in sys.argv:
            sembrar_cartera(db)
            print(f"Cartera de demostración sembrada para los periodos: {', '.join(PERIODOS)}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
