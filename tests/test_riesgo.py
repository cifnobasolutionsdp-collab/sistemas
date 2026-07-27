"""Pruebas de los cálculos de riesgo y del proceso de carga."""
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402

from app import models  # noqa: E402
from app.carga import cargar_cartera_csv  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.riesgo.provisionamiento import calcular_provisionamiento, clasificar_por_mora  # noqa: E402
from app.riesgo.var import calcular_var, indice_herfindahl  # noqa: E402


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    sesion = SessionLocal()
    yield sesion
    sesion.close()
    Base.metadata.drop_all(bind=engine)


def _catalogos_minimos(db):
    region = models.Region(clave="R1", nombre="Región 1")
    db.add(region)
    db.flush()
    plaza = models.Plaza(clave="P1", nombre="Plaza 1", region_id=region.id)
    db.add(plaza)
    db.flush()
    sucursal = models.Sucursal(clave="S1", nombre="Sucursal 1", plaza_id=plaza.id)
    tipo = models.TipoCartera(clave="CONS", nombre="Consumo")
    db.add_all([sucursal, tipo])
    db.flush()
    producto = models.ProductoCredito(clave="PR1", nombre="Producto 1", tipo_cartera_id=tipo.id)
    moneda = models.Moneda(clave="MXN", nombre="Peso", tipo_cambio=1.0)
    actividad = models.Actividad(clave="A1", nombre="Actividad 1", sector_economico="Comercio")
    localidad = models.Localidad(clave="L1", nombre="Localidad 1")
    garantia = models.Garantia(clave="G1", nombre="Líquida", tipo="Líquida", porcentaje_cobertura=50.0)
    db.add_all([producto, moneda, actividad, localidad, garantia])
    db.flush()

    calif_a = models.CalificacionCredito(
        clave="A", mora_min=0, mora_max=30, probabilidad_incumplimiento=2.0, severidad=50.0
    )
    calif_e = models.CalificacionCredito(
        clave="E", mora_min=31, mora_max=None, probabilidad_incumplimiento=100.0, severidad=100.0
    )
    db.add_all([calif_a, calif_e])
    db.flush()
    db.add_all(
        [
            models.ReservaPreventiva(calificacion_id=calif_a.id, porcentaje_reserva=0.5),
            models.ReservaPreventiva(calificacion_id=calif_e.id, porcentaje_reserva=100.0),
        ]
    )
    db.commit()
    return {
        "producto": producto, "sucursal": sucursal, "moneda": moneda,
        "actividad": actividad, "localidad": localidad, "garantia": garantia,
        "calificaciones": [calif_a, calif_e],
    }


def _prestamo(cat, folio, vigente, vencido, mora, garantia=None):
    return models.Prestamo(
        periodo="2026-06",
        folio=folio,
        socio=f"Socio {folio}",
        producto_id=cat["producto"].id,
        sucursal_id=cat["sucursal"].id,
        moneda_id=cat["moneda"].id,
        actividad_id=cat["actividad"].id,
        localidad_id=cat["localidad"].id,
        garantia_id=garantia.id if garantia else None,
        monto_original=vigente + vencido,
        saldo_vigente=vigente,
        saldo_vencido=vencido,
        dias_mora=mora,
        plazo_meses=12,
        tasa_anual=20.0,
        fecha_otorgamiento=date(2025, 6, 1),
        fecha_vencimiento=date(2026, 6, 1),
    )


def test_clasificar_por_mora(db):
    cat = _catalogos_minimos(db)
    calificaciones = cat["calificaciones"]
    assert clasificar_por_mora(0, calificaciones).clave == "A"
    assert clasificar_por_mora(30, calificaciones).clave == "A"
    assert clasificar_por_mora(31, calificaciones).clave == "E"
    assert clasificar_por_mora(500, calificaciones).clave == "E"


def test_provisionamiento(db):
    cat = _catalogos_minimos(db)
    db.add_all(
        [
            _prestamo(cat, "F1", 100_000.0, 0.0, 0),      # A: 0.5% de 100,000 = 500
            _prestamo(cat, "F2", 0.0, 50_000.0, 90),      # E: 100% de 50,000 = 50,000
        ]
    )
    db.commit()
    resultado = calcular_provisionamiento(db, "2026-06")
    assert resultado["creditos"] == 2
    assert resultado["total_exposicion"] == pytest.approx(150_000.0)
    assert resultado["total_reserva"] == pytest.approx(50_500.0)
    por_clave = {f["calificacion"]: f for f in resultado["desglose"]}
    assert por_clave["A"]["reserva"] == pytest.approx(500.0)
    assert por_clave["E"]["reserva"] == pytest.approx(50_000.0)


def test_var_perdida_esperada_y_estres(db):
    cat = _catalogos_minimos(db)
    # Crédito E (PI=100%, severidad 100%, sin garantía): pérdida segura de 50,000.
    # Crédito A (PI=2%, severidad 50%, garantía 50%): PE = 2% · 25% · 100,000 = 500.
    db.add_all(
        [
            _prestamo(cat, "F1", 100_000.0, 0.0, 0, garantia=cat["garantia"]),
            _prestamo(cat, "F2", 0.0, 50_000.0, 90),
        ]
    )
    db.commit()
    resultado = calcular_var(db, "2026-06", confianza=0.95, simulaciones=500, factores_estres=(1.0, 2.0))
    base = resultado["escenarios"][0]
    assert base["perdida_esperada"] == pytest.approx(50_500.0)
    assert base["var"] >= 50_000.0  # el crédito E siempre incumple
    estres = resultado["escenarios"][1]
    # PI del crédito A se duplica (4%): PE = 50,000 + 1,000
    assert estres["perdida_esperada"] == pytest.approx(51_000.0)
    assert resultado["exposicion_total"] == pytest.approx(150_000.0)

    # Reproducibilidad con la misma semilla
    repetido = calcular_var(db, "2026-06", confianza=0.95, simulaciones=500, factores_estres=(1.0, 2.0))
    assert repetido["escenarios"][0]["var"] == pytest.approx(base["var"])


def test_indice_herfindahl():
    assert indice_herfindahl([100.0]) == pytest.approx(10_000.0)
    assert indice_herfindahl([50.0, 50.0]) == pytest.approx(5_000.0)
    assert indice_herfindahl([1.0] * 100) == pytest.approx(100.0)
    assert indice_herfindahl([]) == 0.0


def test_carga_csv(db):
    _catalogos_minimos(db)
    csv_ok = (
        "periodo,folio,socio,producto,sucursal,moneda,actividad,localidad,garantia,"
        "monto_original,saldo_vigente,saldo_vencido,dias_mora,plazo_meses,tasa_anual,"
        "fecha_otorgamiento,fecha_vencimiento\n"
        "2026-07,X1,Socio Uno,PR1,S1,MXN,A1,L1,G1,10000,9000,0,0,12,20,2026-01-01,2027-01-01\n"
        "2026-07,X2,Socio Dos,NOEXISTE,S1,MXN,A1,L1,,10000,9000,0,0,12,20,2026-01-01,2027-01-01\n"
    )
    carga = cargar_cartera_csv(db, csv_ok.encode("utf-8"), "prueba.csv")
    assert carga.registros == 1
    assert carga.rechazados == 1
    assert carga.estatus == "Parcial"
    assert "NOEXISTE" in carga.mensaje

    # Recarga idempotente: el mismo folio se reemplaza, no se duplica
    carga2 = cargar_cartera_csv(
        db,
        csv_ok.replace(",9000,", ",8000,", 1).encode("utf-8"),
        "prueba2.csv",
    )
    assert carga2.registros == 1
    prestamos = db.query(models.Prestamo).filter_by(periodo="2026-07").all()
    assert len(prestamos) == 1
    assert prestamos[0].saldo_vigente == pytest.approx(8000.0)
