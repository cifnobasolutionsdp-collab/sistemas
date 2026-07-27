"""Pruebas de humo de la aplicación web (rutas principales)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.catalogos_config import CATALOGOS  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


RUTAS = [
    "/",
    "/consultas/plazo",
    "/consultas/monto",
    "/consultas/evolucion",
    "/consultas/distribucion",
    "/consultas/limites",
    "/procesos/carga",
    "/procesos/provisionamiento",
    "/procesos/var",
    "/procesos/analisis-var",
    "/reportes/ejecutivo",
    "/reportes/distribucion",
    "/reportes/personalizado",
    "/reportes/personalizado.csv",
]


@pytest.mark.parametrize("ruta", RUTAS)
def test_rutas_principales(cliente, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200, f"{ruta}: {respuesta.status_code}"


@pytest.mark.parametrize("slug", list(CATALOGOS))
def test_catalogos(cliente, slug):
    assert cliente.get(f"/catalogos/{slug}").status_code == 200
    assert cliente.get(f"/catalogos/{slug}/nuevo").status_code == 200


def test_catalogo_inexistente(cliente):
    assert cliente.get("/catalogos/no-existe").status_code == 404


def test_alta_en_catalogo(cliente):
    respuesta = cliente.post(
        "/catalogos/regiones/nuevo",
        data={"clave": "TEST", "nombre": "Región de prueba"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    listado = cliente.get("/catalogos/regiones")
    assert "Región de prueba" in listado.text
