"""Pruebas del sistema de Reclutamiento y Selección (Fast Apply)."""
import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("RECLUTAMIENTO_DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from reclutamiento import models  # noqa: E402
from reclutamiento.catalogos_config import CATALOGOS  # noqa: E402
from reclutamiento.database import SessionLocal  # noqa: E402
from reclutamiento.main import app  # noqa: E402
from reclutamiento.plantillas_proceso import PLANTILLAS, generar_descripcion  # noqa: E402


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def proceso_id(cliente):
    """Proceso Fast Apply creado desde la plantilla de Asesor de Crédito."""
    respuesta = cliente.post(
        "/procesos/crear",
        data={
            "tipo": "fast_apply",
            "posicion": "Asesor de Crédito",
            "jornada": "Jornada Completa",
            "modalidad": "Presencial",
            "descripcion": "",
            "generar_ia": "1",
            "plantilla": "asesor-credito",
            "vacantes": "2",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    pid = int(respuesta.headers["location"].rstrip("/").split("/")[-1])
    # Publicar el proceso para que reciba postulaciones
    respuesta = cliente.post(
        f"/procesos/{pid}/publicacion",
        data={
            "fecha_publicacion": date.today().isoformat(),
            "fecha_fin": (date.today() + timedelta(days=30)).isoformat(),
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    return pid


def _token(pid):
    db = SessionLocal()
    try:
        return db.get(models.Proceso, pid).token
    finally:
        db.close()


RUTAS = ["/", "/procesos", "/procesos/nuevo", "/candidatos"]


@pytest.mark.parametrize("ruta", RUTAS)
def test_rutas_principales(cliente, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200, f"{ruta}: {respuesta.status_code}"


@pytest.mark.parametrize("slug", list(CATALOGOS))
def test_catalogos(cliente, slug):
    assert cliente.get(f"/catalogos/{slug}").status_code == 200
    assert cliente.get(f"/catalogos/{slug}/nuevo").status_code == 200


def test_alta_en_catalogo(cliente):
    respuesta = cliente.post(
        "/catalogos/sucursales/nuevo",
        data={"clave": "TEST", "nombre": "Sucursal de prueba", "plaza": "León", "estado": "Gto."},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "Sucursal de prueba" in cliente.get("/catalogos/sucursales").text


def test_proceso_creado_desde_plantilla(cliente, proceso_id):
    pagina = cliente.get(f"/procesos/{proceso_id}")
    assert pagina.status_code == 200
    assert "Asesor de Crédito" in pagina.text
    plantilla = PLANTILLAS["asesor-credito"]
    for pregunta in plantilla.preguntas:
        assert pregunta.texto[:40] in pagina.text
    # Descripción autogenerada por el asistente
    assert "Estamos en búsqueda" in pagina.text


def test_vistas_del_proceso(cliente, proceso_id):
    for sufijo in ("", "/editar", "/mensajes", "/publicacion", "/poster"):
        assert cliente.get(f"/procesos/{proceso_id}{sufijo}").status_code == 200
    assert "<svg" in cliente.get(f"/procesos/{proceso_id}/poster").text


def test_flujo_fast_apply_completo(cliente, proceso_id):
    """El candidato conversa, responde afirmativamente y queda postulado."""
    token = _token(proceso_id)
    assert cliente.get(f"/postular/{token}").status_code == 200

    respuesta = cliente.post(
        f"/postular/{token}/iniciar",
        data={"nombre": "Andrea Rodríguez", "telefono": "5512340001"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    p = int(respuesta.headers["location"].split("p=")[1])

    # Resumen de experiencia (paso CV)
    cliente.post(
        f"/postular/{token}/responder",
        data={"p": p, "texto": "3 años colocando crédito en una SOFIPO."},
    )

    db = SessionLocal()
    try:
        postulacion = db.get(models.Postulacion, p)
        while postulacion.paso.startswith("cuestionario:"):
            indice = int(postulacion.paso.split(":")[1])
            pregunta = postulacion.proceso.preguntas[indice]
            if pregunta.tipo == "cerrada":
                opcion = max(
                    (o for o in pregunta.opciones if not o.excluyente),
                    key=lambda o: o.peso,
                )
                datos = {"p": p, "opcion_id": opcion.id}
            else:
                datos = {"p": p, "texto": "Recuperé cartera vencida con planes de pago."}
            cliente.post(f"/postular/{token}/responder", data=datos)
            db.expire_all()
            postulacion = db.get(models.Postulacion, p)

        assert postulacion.estado == "postulado"
        # Todas las respuestas con peso máximo → 100% de adecuación
        assert postulacion.adecuacion == 100.0
        assert postulacion.resumen_cv
        assert postulacion.completada_en is not None
    finally:
        db.close()

    # CV autogenerado y detalle del candidato
    assert cliente.get(f"/candidatos/{p}").status_code == 200
    cv = cliente.get(f"/candidatos/{p}/cv")
    assert cv.status_code == 200
    assert "Andrea Rodríguez" in cv.text

    # Cambio de estatus del candidato
    respuesta = cliente.post(
        f"/candidatos/{p}/estado", data={"estado": "preseleccionado"}, follow_redirects=False
    )
    assert respuesta.status_code == 303


def test_descarte_por_pregunta_excluyente(cliente, proceso_id):
    """Responder una opción excluyente descarta al candidato automáticamente."""
    token = _token(proceso_id)
    respuesta = cliente.post(
        f"/postular/{token}/iniciar",
        data={"nombre": "Luis Hernández"},
        follow_redirects=False,
    )
    p = int(respuesta.headers["location"].split("p=")[1])
    cliente.post(f"/postular/{token}/responder", data={"p": p, "texto": ""})

    db = SessionLocal()
    try:
        postulacion = db.get(models.Postulacion, p)
        pregunta = postulacion.proceso.preguntas[0]
        excluyente = next(o for o in pregunta.opciones if o.excluyente)
        cliente.post(
            f"/postular/{token}/responder", data={"p": p, "opcion_id": excluyente.id}
        )
        db.expire_all()
        postulacion = db.get(models.Postulacion, p)
        assert postulacion.estado == "descartado"
        assert postulacion.paso == "fin"
    finally:
        db.close()


def test_copiar_proceso(cliente, proceso_id):
    respuesta = cliente.post(
        "/procesos/crear",
        data={
            "tipo": "fast_apply",
            "posicion": "Asesor de Crédito (copia)",
            "descripcion": "Vacante copiada.",
            "copiar": str(proceso_id),
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    nuevo_id = int(respuesta.headers["location"].rstrip("/").split("/")[-1])
    db = SessionLocal()
    try:
        original = db.get(models.Proceso, proceso_id)
        copia = db.get(models.Proceso, nuevo_id)
        assert len(copia.preguntas) == len(original.preguntas)
        assert copia.token != original.token
    finally:
        db.close()


def test_proceso_sin_publicar_no_recibe_postulaciones(cliente):
    respuesta = cliente.post(
        "/procesos/crear",
        data={"tipo": "estandar", "posicion": "Contador General", "descripcion": "x"},
        follow_redirects=False,
    )
    pid = int(respuesta.headers["location"].rstrip("/").split("/")[-1])
    token = _token(pid)
    assert cliente.get(f"/postular/{token}").status_code == 410
    respuesta = cliente.post(
        f"/postular/{token}/iniciar", data={"nombre": "X"}, follow_redirects=False
    )
    assert respuesta.status_code == 410


def test_generar_descripcion():
    texto = generar_descripcion("Cajero", "Operaciones", "Jornada Completa", "Presencial", "Matriz")
    assert "Cajero" in texto and "Operaciones" in texto and "Matriz" in texto


def test_google_for_jobs_jsonld(cliente, proceso_id):
    """La página de postulación incluye datos estructurados JobPosting para Google."""
    token = _token(proceso_id)
    pagina = cliente.get(f"/postular/{token}")
    assert '"@type": "JobPosting"' in pagina.text
    assert '"directApply": true' in pagina.text
    assert "Asesor de Cr" in pagina.text


def test_mensajes_personalizados(cliente, proceso_id):
    respuesta = cliente.post(
        f"/procesos/{proceso_id}/mensajes",
        data={
            "msg_bienvenida": "¡Hola {{nombre}}! Bienvenido a {{empresa}}.",
            "solicitar_cv": "1",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    pagina = cliente.get(f"/procesos/{proceso_id}/mensajes")
    assert "¡Hola Andrea! Bienvenido a" in pagina.text
