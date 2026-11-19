"""Pruebas del módulo de Sistema de Evaluación y Monitoreo Financiero."""
import io
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.monitoreo.estrategias import estrategias, interrelacion, plan_de_accion  # noqa: E402
from app.monitoreo.ifrs9 import calcular_pce  # noqa: E402
from app.monitoreo.importacion import a_numero, importar_balanza, importar_estados  # noqa: E402
from app.monitoreo.indicadores import INDICADORES, calcular_indicadores  # noqa: E402
from app.monitoreo.modelos import Entidad  # noqa: E402
from app.monitoreo.rubros import agregados  # noqa: E402

Base.metadata.create_all(bind=engine)

BALANZA = """cuenta,descripcion,saldo_final
1,ACTIVO,1000
11,Disponibilidades,150
1101,Caja,10
1102,Bancos,140
1201,Inversiones CP,50
1301,Cartera etapa 1,700
1302,Cartera etapa 2,40
1303,Cartera etapa 3,60
1304,Estimacion,50
1601,Activo fijo,50
2101,Depositos vista,300
2102,Depositos plazo,450
2201,Prestamos bancarios,20
2301,Acreedores,10
3101,Capital social,100
3201,Fondo de reserva,80
3202,Resultados anteriores,10
4101,Intereses cartera,90
4102,Intereses inversiones,5
5101,Intereses depositos,30
5301,Estimacion preventiva,10
5401,Gastos de administracion,25
"""


@pytest.fixture()
def db():
    sesion = SessionLocal()
    yield sesion
    sesion.close()


def _entidad(db, clave, tipo="SOCAP"):
    ent = db.query(Entidad).filter_by(clave=clave).one_or_none()
    if ent is None:
        ent = Entidad(clave=clave, nombre=f"Entidad {clave}", tipo=tipo)
        db.add(ent)
        db.commit()
    return ent


def test_a_numero_formatos():
    assert a_numero("1,234.50") == 1234.5
    assert a_numero("1.234,50") == 1234.5
    assert a_numero("$(1,000)") == -1000
    assert a_numero("12%") == pytest.approx(0.12)
    assert a_numero("") is None
    assert a_numero("N/A") is None


def test_importar_balanza_omite_mayores_y_cuadra(db):
    ent = _entidad(db, "T1")
    res = importar_balanza(db, ent, date(2026, 6, 30), BALANZA.encode(), "balanza.csv")
    assert res.estatus == "Exitosa", res.mensajes
    r = res.rubros
    assert r["caja"] == 10 and r["bancos"] == 140  # la cuenta 11 (mayor) no se duplica
    assert r["estimaciones"] == 50
    # Balanza no cerrada: resultado = ingresos − gastos
    assert r["resultado_ejercicio"] == pytest.approx(95 - 65)
    ag = agregados(r)
    assert ag["activo_total"] == pytest.approx(10 + 140 + 50 + 750 + 50)
    assert ag["descuadre"] == pytest.approx(0)


def test_balanza_con_signo_y_columnas_separadas(db):
    ent = _entidad(db, "T2")
    lineas = ["cuenta,descripcion,saldo_deudor,saldo_acreedor"]
    for linea in BALANZA.strip().splitlines()[1:]:
        cuenta, desc, saldo = linea.split(",")
        acreedora = cuenta[0] in "234" or cuenta.startswith("1304")
        lineas.append(f"{cuenta},{desc},{'' if acreedora else saldo},{saldo if acreedora else ''}")
    res = importar_balanza(db, ent, date(2026, 6, 30), "\n".join(lineas).encode(), "balanza2.csv")
    assert res.estatus == "Exitosa", res.mensajes
    assert res.rubros["estimaciones"] == 50
    assert res.rubros["depositos_plazo"] == 450
    assert agregados(res.rubros)["descuadre"] == pytest.approx(0)


def test_balanza_codigos_longitud_fija(db):
    ent = _entidad(db, "T3")
    texto = (
        "cuenta;descripcion;saldo_final\n"
        "1101-000;Caja (mayor);30\n1101-001;Caja general;20\n1101-002;Caja chica;10\n"
        "1301-000;Cartera etapa 1;100\n1301-001;Consumo;100\n"
        "2101-000;Depositos;130\n2101-001;Ahorro;130\n"
    )
    res = importar_balanza(db, ent, date(2026, 3, 31), texto.encode(), "fija.csv")
    assert res.rubros["caja"] == 30
    assert res.rubros["cartera_etapa1"] == 100
    assert res.rubros["depositos_vista"] == 130


def test_cuenta_sin_mapeo_es_parcial(db):
    ent = _entidad(db, "T4")
    res = importar_balanza(db, ent, date(2026, 3, 31), b"cuenta,saldo_final\n9901,500\n1101,10\n", "x.csv")
    assert res.estatus == "Parcial"
    assert res.sin_mapeo and res.sin_mapeo[0][0] == "9901"


def test_importar_estados_y_parametros(db):
    ent = _entidad(db, "T5")
    importar_balanza(db, ent, date(2026, 6, 30), BALANZA.encode(), "balanza.csv")
    texto = "clave,importe\nmora_1_12,45\nmora_mas_12,15\nasociados,1200\ninflacion,4.5\ntasa_mercado,8\nclave_rara,1\n"
    res = importar_estados(db, ent, date(2026, 6, 30), texto.encode(), "compl.csv")
    assert res.estatus == "Parcial"  # por la clave no reconocida
    estado = db.get(type(ent.estados[0]), res.estado_id)
    assert estado.inflacion == pytest.approx(0.045)
    datos = estado.datos()
    assert datos["mora_1_12"] == 45 and datos["caja"] == 10  # conserva la balanza


def test_indicadores_principales(db):
    ent = _entidad(db, "T5")
    estado = ent.estados[-1]
    res = calcular_indicadores(db, estado)
    pc = res["por_codigo"]
    at = 1000
    assert pc["E1"]["valor"] == pytest.approx((800 - 50) / at)
    assert pc["A1"]["valor"] == pytest.approx(60 / 800)  # mora 1-12 + >12
    assert pc["A1"]["estatus"] == "deficiente"
    assert pc["P1"]["valor"] == pytest.approx(1.0)
    assert pc["P2"]["valor"] == pytest.approx((50 - 15) / 45)
    # R1: anualizado a 6 meses sobre la cartera neta (un solo punto = saldo actual)
    assert res["factor"] == pytest.approx(2)
    assert pc["R1"]["valor"] == pytest.approx(90 * 2 / 750)
    assert pc["R5"]["estatus"] in ("cumple", "alerta", "deficiente")  # evaluado contra la inflación
    assert pc["S1"]["estatus"] == "na"  # sin periodo base
    assert 0 < res["pct_deficientes"] < 1
    assert pc["K1"]["estatus"] == "na"  # no aplica a SOCAP
    # La brecha de A1 indica cuánto reducir la morosidad
    assert pc["A1"]["brecha"] == pytest.approx(0.05 * 800 - 60)


def test_crecimiento_anualizado(db):
    ent = _entidad(db, "T6")
    importar_balanza(db, ent, date(2025, 12, 31), BALANZA.encode(), "b0.csv")
    mas = BALANZA.replace("1301,Cartera etapa 1,700", "1301,Cartera etapa 1,770").replace("2102,Depositos plazo,450", "2102,Depositos plazo,520")
    importar_balanza(db, ent, date(2026, 6, 30), mas.encode(), "b1.csv")
    res = calcular_indicadores(db, ent.estados[-1])
    neta0, neta1 = 750, 820
    assert res["por_codigo"]["S1"]["valor"] == pytest.approx((neta1 / neta0) ** 2 - 1)


def test_pce_ifrs9():
    datos = {"cartera_etapa1": 1000, "cartera_etapa2": 100, "cartera_etapa3": 50, "estimaciones": 60}
    params = {"pd_etapa1": 0.02, "pd_etapa2": 0.2, "pd_etapa3": 1.0, "lgd": 0.5, "escenarios": [{"nombre": "Base", "peso": 1, "factor": 1}]}
    pce = calcular_pce(datos, params)
    assert pce["pce_total"] == pytest.approx(1000 * 0.02 * 0.5 + 100 * 0.2 * 0.5 + 50 * 0.5)
    assert pce["deficit"] == pytest.approx(55 - 60 if 55 > 60 else 0)
    # Asignación estimada: primero etapa 3, luego 2, remanente a 1
    assert pce["etapas"][2]["reserva"] == pytest.approx(25)
    assert pce["etapas"][1]["reserva"] == pytest.approx(10)
    assert pce["etapas"][0]["reserva"] == pytest.approx(25)
    # PCE reportada por la entidad tiene prioridad
    propia = calcular_pce({**datos, "pe_etapa1": 5, "pe_etapa2": 5, "pe_etapa3": 40}, params)
    assert propia["pce_total"] == 50 and propia["fuente_pce"].startswith("Reportada")


def test_escenario_pesimista_aumenta_pce():
    pce = calcular_pce({"cartera_etapa1": 1000, "cartera_etapa2": 100, "estimaciones": 0})
    por_nombre = {e["nombre"]: e["pce"] for e in pce["escenarios"]}
    assert por_nombre["Pesimista"] > por_nombre["Base"] > por_nombre["Optimista"]


def test_estrategias_e_interrelacion_cubren_indicadores():
    for ind in INDICADORES:
        assert estrategias(ind.codigo), f"{ind.codigo} sin estrategias"
    assert "E1" in interrelacion("P1")["afecta"]
    assert "R10" in interrelacion("P1")["afectado_por"]


def test_plan_prioriza_deficientes(db):
    ent = _entidad(db, "T5")
    res = calcular_indicadores(db, ent.estados[-1])
    plan = plan_de_accion(res)
    estatus = [p["fila"]["estatus"] for p in plan]
    assert estatus == sorted(estatus, key=lambda e: e != "deficiente")
    assert plan[0]["prioridad"] == "Alta"


# ---------------------------------------------------------------- web
@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


def test_flujo_web_completo(cliente):
    r = cliente.post("/monitoreo/entidades", data={"clave": "WEB1", "nombre": "Caja Web", "tipo": "SOCAP"}, follow_redirects=False)
    assert r.status_code == 303
    sesion = SessionLocal()
    ent_id = sesion.query(Entidad).filter_by(clave="WEB1").one().id
    sesion.close()
    r = cliente.post(
        "/monitoreo/carga",
        data={"entidad_id": ent_id, "fecha_corte": "2026-06-30", "tipo": "balanza", "inflacion": "4"},
        files={"archivo": ("balanza.csv", BALANZA.encode(), "text/csv")},
    )
    assert r.status_code == 200 and "exitosa" in r.text.lower()
    # Plantilla xlsx llenada e importada
    plantilla = cliente.get("/monitoreo/plantilla/estados.xlsx")
    libro = load_workbook(io.BytesIO(plantilla.content))
    hoja = libro["Datos complementarios"]
    for fila in hoja.iter_rows(min_row=2):
        if fila[0].value == "mora_1_12":
            fila[3].value = 30
        if fila[0].value == "mora_mas_12":
            fila[3].value = 5
    salida = io.BytesIO()
    libro.save(salida)
    r = cliente.post(
        "/monitoreo/carga",
        data={"entidad_id": ent_id, "fecha_corte": "2026-06-30", "tipo": "estados"},
        files={"archivo": ("compl.xlsx", salida.getvalue(), "application/octet-stream")},
    )
    assert r.status_code == 200 and "exitosa" in r.text.lower(), r.text[-2000:]

    for ruta in [
        "/monitoreo", "/monitoreo/carga", "/monitoreo/metas", "/monitoreo/metas?tipo=SOFOM", "/monitoreo/mapeo",
        f"/monitoreo/entidades/{ent_id}", f"/monitoreo/entidades/{ent_id}/plan", f"/monitoreo/entidades/{ent_id}/rubros",
        f"/monitoreo/entidades/{ent_id}/indicador/A1", f"/monitoreo/entidades/{ent_id}/indicador/I7", f"/monitoreo/entidades/{ent_id}/ifrs9",
        "/monitoreo/plantilla/balanza.xlsx",
    ]:
        assert cliente.get(ruta).status_code == 200, ruta

    excel = cliente.get(f"/monitoreo/entidades/{ent_id}/excel")
    libro = load_workbook(io.BytesIO(excel.content))
    assert {"Indicadores", "Plan de acción", "IFRS 9", "Rubros"} <= set(libro.sheetnames)

    # Metas personalizadas y parámetros IFRS 9
    assert cliente.post("/monitoreo/metas", data={"tipo": "SOCAP", "min_A1": "", "max_A1": "10"}, follow_redirects=False).status_code == 303
    r = cliente.post(f"/monitoreo/entidades/{ent_id}/ifrs9", data={"pd_etapa1": "2", "lgd": "40", "accion": "guardar"}, follow_redirects=False)
    assert r.status_code == 303
    sesion = SessionLocal()
    ent = sesion.get(Entidad, ent_id)
    assert ent.params_ifrs9()["lgd"] == pytest.approx(0.40)
    res = calcular_indicadores(sesion, ent.estados[-1])
    assert res["por_codigo"]["A1"]["maximo"] == pytest.approx(0.10)
    sesion.close()
    cliente.post("/monitoreo/metas", data={"tipo": "SOCAP", "min_A1": "", "max_A1": ""})


def test_mapeo_por_entidad(cliente):
    sesion = SessionLocal()
    ent = _entidad(sesion, "MAP1")
    ent_id = ent.id
    sesion.close()
    assert cliente.post("/monitoreo/mapeo", data={"prefijo": "9901", "rubro": "otros_activos", "entidad_id": str(ent_id)}, follow_redirects=False).status_code == 303
    sesion = SessionLocal()
    res = importar_balanza(sesion, sesion.get(Entidad, ent_id), date(2026, 1, 31), b"cuenta,saldo_final\n9901,500\n", "m.csv")
    assert res.rubros.get("otros_activos") == 500
    sesion.close()
