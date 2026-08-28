"""Pruebas del portal de suscripciones para organizaciones financieras."""
import os

os.environ["PORTAL_DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from portal.database import Base, engine
from portal.main import app


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app, follow_redirects=False)


# ------------------------------------------------------------------ #
# Landing page                                                        #
# ------------------------------------------------------------------ #
def test_landing_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "cifnoba" in r.text
    assert "Fast Apply" in r.text
    assert "SOCAPS" in r.text


def test_landing_planes():
    r = client.get("/")
    assert "Básico" in r.text
    assert "Profesional" in r.text
    assert "Empresarial" in r.text


# ------------------------------------------------------------------ #
# Registro                                                            #
# ------------------------------------------------------------------ #
def test_registro_form():
    r = client.get("/registro")
    assert r.status_code == 200
    assert "Registra tu institución" in r.text


def _datos_registro(**overrides):
    datos = {
        "org_nombre": "SOCAP de Prueba",
        "org_rfc": "SPR010101AAA",
        "org_tipo": "socap",
        "org_telefono": "5551234567",
        "org_email": "contacto@socapprueba.com",
        "org_num_empleados": "11-50",
        "usuario_nombre": "Admin Prueba",
        "usuario_email": "admin@socapprueba.com",
        "usuario_password": "password123",
        "usuario_password2": "password123",
        "plan": "profesional",
    }
    datos.update(overrides)
    return datos


def test_registro_exitoso():
    r = client.post("/registro", data=_datos_registro())
    assert r.status_code == 303
    assert r.headers["location"] == "/panel"
    assert "cifnoba_session" in r.cookies


def test_registro_rfc_duplicado():
    client.post("/registro", data=_datos_registro())
    r = client.post("/registro", data=_datos_registro(
        usuario_email="otro@email.com",
    ))
    assert r.status_code == 200
    assert "Ya existe una organización" in r.text


def test_registro_email_duplicado():
    client.post("/registro", data=_datos_registro())
    r = client.post("/registro", data=_datos_registro(
        org_rfc="OTR010101BBB",
    ))
    assert r.status_code == 200
    assert "Ya existe una cuenta" in r.text


def test_registro_password_corta():
    r = client.post("/registro", data=_datos_registro(
        usuario_password="corta",
        usuario_password2="corta",
    ))
    assert r.status_code == 200
    assert "8 caracteres" in r.text


def test_registro_password_no_coincide():
    r = client.post("/registro", data=_datos_registro(
        usuario_password2="otrapassword",
    ))
    assert r.status_code == 200
    assert "no coinciden" in r.text


# ------------------------------------------------------------------ #
# Login / Logout                                                      #
# ------------------------------------------------------------------ #
def test_login_form():
    r = client.get("/login")
    assert r.status_code == 200
    assert "Iniciar sesión" in r.text


def test_login_exitoso():
    client.post("/registro", data=_datos_registro())
    c = TestClient(app, follow_redirects=False)
    r = c.post("/login", data={
        "email": "admin@socapprueba.com",
        "password": "password123",
    })
    assert r.status_code == 303
    assert r.headers["location"] == "/panel"
    assert "cifnoba_session" in r.cookies


def test_login_fallido():
    r = client.post("/login", data={
        "email": "noexiste@email.com",
        "password": "wrongpassword",
    })
    assert r.status_code == 200
    assert "incorrectos" in r.text


def test_logout():
    client.post("/registro", data=_datos_registro())
    r = client.get("/logout")
    assert r.status_code == 303
    assert r.headers["location"] == "/"


# ------------------------------------------------------------------ #
# Panel (requiere login)                                              #
# ------------------------------------------------------------------ #
def _login_client():
    c = TestClient(app, follow_redirects=False)
    c.post("/registro", data=_datos_registro())
    return c


def test_panel_sin_login():
    c = TestClient(app, follow_redirects=False, cookies={})
    r = c.get("/panel")
    assert r.status_code == 303
    assert "/login" in r.headers["location"]


def test_panel_con_login():
    c = _login_client()
    r = c.get("/panel", follow_redirects=False)
    assert r.status_code == 200
    assert "SOCAP de Prueba" in r.text
    assert "Profesional" in r.text


def test_suscripcion_page():
    c = _login_client()
    r = c.get("/panel/suscripcion")
    assert r.status_code == 200
    assert "Profesional" in r.text
    assert "$4,999" in r.text


def test_cambiar_plan():
    c = _login_client()
    r = c.post("/panel/suscripcion/cambiar", data={"nuevo_plan": "empresarial"})
    assert r.status_code == 303
    r = c.get("/panel/suscripcion")
    assert "Empresarial" in r.text


def test_organizacion_editar():
    c = _login_client()
    r = c.get("/panel/organizacion")
    assert r.status_code == 200
    assert "SOCAP de Prueba" in r.text


def test_organizacion_guardar():
    c = _login_client()
    r = c.post("/panel/organizacion", data={
        "nombre": "SOCAP Actualizada",
        "telefono": "5559876543",
        "email": "nuevo@email.com",
        "sitio_web": "https://socapactualizada.com",
        "direccion": "Calle 1 #100",
        "num_empleados": "51-200",
    })
    assert r.status_code == 200
    assert "guardaron correctamente" in r.text
    assert "SOCAP Actualizada" in r.text


# ------------------------------------------------------------------ #
# Auth: hashing de contraseñas                                        #
# ------------------------------------------------------------------ #
def test_password_hashing():
    from portal.auth import hash_password, verify_password

    hashed = hash_password("mi_clave_segura")
    assert verify_password("mi_clave_segura", hashed)
    assert not verify_password("clave_incorrecta", hashed)


# ------------------------------------------------------------------ #
# Redirección si ya está autenticado                                  #
# ------------------------------------------------------------------ #
def test_login_redirige_si_autenticado():
    c = _login_client()
    r = c.get("/login", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/panel"


def test_registro_redirige_si_autenticado():
    c = _login_client()
    r = c.get("/registro", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/panel"
