"""Siembra catálogos y procesos de demostración del sistema de reclutamiento.

Uso:  python scripts/seed_reclutamiento.py

Crea sucursales, áreas y canales de publicación típicos de una institución
financiera popular, tres procesos Fast Apply a partir de las plantillas del
sector y postulaciones simuladas (con candidatos postulados, descartados por
preguntas excluyentes, preseleccionados y contratados).
"""
from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reclutamiento import chatbot, models  # noqa: E402
from reclutamiento.database import Base, SessionLocal, engine  # noqa: E402
from reclutamiento.plantillas_proceso import PLANTILLAS  # noqa: E402

rng = random.Random(2026)

CANDIDATOS = [
    ("Andrea Rodríguez", "55 1234 0001", "andrea.rodriguez@example.com"),
    ("Luis Hernández", "55 1234 0002", "luis.hernandez@example.com"),
    ("María Fernanda López", "55 1234 0003", "mafer.lopez@example.com"),
    ("Carlos Ramírez", "55 1234 0004", "carlos.ramirez@example.com"),
    ("Sofía Torres", "55 1234 0005", "sofia.torres@example.com"),
    ("Jorge Castañeda", "55 1234 0006", "jorge.castaneda@example.com"),
    ("Paola Jiménez", "55 1234 0007", "paola.jimenez@example.com"),
    ("Miguel Ángel Ruiz", "55 1234 0008", "miguel.ruiz@example.com"),
]

EXPERIENCIAS = [
    "Trabajé 3 años como asesor en una SOFIPO regional, colocando crédito grupal "
    "e individual con cartera sana.",
    "Tengo experiencia en ventanilla bancaria y manejo de efectivo, con arqueos "
    "diarios sin diferencias.",
    "Colaboré en el área de riesgos de una SOCAP, apoyando la calificación de "
    "cartera y reportes a CNBV.",
    "",
]


def sembrar_catalogos(db) -> None:
    db.add_all(
        [
            models.Sucursal(clave="MATRIZ", nombre="Matriz", plaza="León", estado="Guanajuato"),
            models.Sucursal(clave="CENTRO", nombre="Sucursal Centro", plaza="Morelia", estado="Michoacán"),
            models.Sucursal(clave="NORTE", nombre="Sucursal Norte", plaza="Zacatecas", estado="Zacatecas"),
        ]
    )
    db.add_all(
        [
            models.Area(clave="CRED", nombre="Crédito"),
            models.Area(clave="OPER", nombre="Operaciones"),
            models.Area(clave="RIES", nombre="Riesgos"),
            models.Area(clave="COM", nombre="Comercial"),
            models.Area(clave="DIR", nombre="Dirección de Sucursales"),
        ]
    )
    db.add_all(
        [
            models.CanalPublicacion(clave="COMPU", nombre="Computrabajo", tipo="portal"),
            models.CanalPublicacion(clave="OCC", nombre="OCC Mundial", tipo="portal"),
            models.CanalPublicacion(clave="GJOBS", nombre="Google for Jobs", tipo="portal"),
            models.CanalPublicacion(clave="MICRO", nombre="Micrositio de empleo", tipo="micrositio"),
            models.CanalPublicacion(clave="FB", nombre="Facebook", tipo="red_social"),
            models.CanalPublicacion(clave="LI", nombre="LinkedIn", tipo="red_social"),
            models.CanalPublicacion(clave="MAIL", nombre="Divulgación por correo", tipo="correo"),
            models.CanalPublicacion(clave="INT", nombre="Reclutamiento interno", tipo="interno"),
        ]
    )
    db.commit()


def crear_proceso_desde_plantilla(db, slug: str, sucursal_id: int) -> models.Proceso:
    plantilla = PLANTILLAS[slug]
    area = (
        db.query(models.Area).filter(models.Area.nombre == plantilla.area).one_or_none()
    )
    proceso = models.Proceso(
        tipo="fast_apply",
        posicion=plantilla.posicion,
        area_id=area.id if area else None,
        sucursal_id=sucursal_id,
        jornada=plantilla.jornada,
        modalidad=plantilla.modalidad,
        descripcion=plantilla.descripcion,
        fecha_publicacion=date.today() - timedelta(days=5),
        fecha_fin=date.today() + timedelta(days=30),
    )
    db.add(proceso)
    db.flush()
    for orden, pp in enumerate(plantilla.preguntas, start=1):
        pregunta = models.PreguntaFiltro(
            proceso_id=proceso.id, orden=orden, texto=pp.texto, tipo=pp.tipo
        )
        db.add(pregunta)
        db.flush()
        for op in pp.opciones:
            db.add(
                models.OpcionRespuesta(
                    pregunta_id=pregunta.id,
                    texto=op.texto,
                    peso=op.peso,
                    excluyente=op.excluyente,
                )
            )
    # Canales de difusión de ejemplo
    for canal in db.query(models.CanalPublicacion).limit(4):
        db.add(models.CanalProceso(proceso_id=proceso.id, canal_id=canal.id))
    db.commit()
    db.refresh(proceso)
    return proceso


def simular_postulaciones(db, proceso: models.Proceso, cuantas: int) -> None:
    for nombre, telefono, correo in rng.sample(CANDIDATOS, cuantas):
        postulacion = chatbot.iniciar_postulacion(db, proceso, nombre, telefono, correo)
        if postulacion.paso == "cv":
            chatbot.registrar_cv(db, postulacion, rng.choice(EXPERIENCIAS))
        while postulacion.paso.startswith("cuestionario:"):
            pregunta = chatbot.pregunta_actual(postulacion)
            if pregunta.tipo == "cerrada":
                # 80% de respuestas afirmativas para producir mezcla de resultados
                opciones = sorted(pregunta.opciones, key=lambda o: -o.peso)
                opcion = opciones[0] if rng.random() < 0.8 else opciones[-1]
                chatbot.responder_pregunta(db, postulacion, opcion_id=opcion.id)
            else:
                chatbot.responder_pregunta(
                    db, postulacion, texto=rng.choice(EXPERIENCIAS[:3])
                )
        db.refresh(postulacion)
        if postulacion.estado == "postulado" and (postulacion.adecuacion or 0) >= 80:
            postulacion.estado = rng.choice(["preseleccionado", "contratado", "postulado"])
    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Proceso).count() > 0:
            print("La base ya contiene procesos; no se siembra de nuevo.")
            return
        sembrar_catalogos(db)
        sucursales = db.query(models.Sucursal).all()
        procesos = [
            crear_proceso_desde_plantilla(db, "asesor-credito", sucursales[0].id),
            crear_proceso_desde_plantilla(db, "cajero", sucursales[1].id),
            crear_proceso_desde_plantilla(db, "promotor-captacion", sucursales[2].id),
        ]
        for proceso, cuantas in zip(procesos, (5, 4, 3)):
            simular_postulaciones(db, proceso, cuantas)
        print("Datos de demostración sembrados:")
        for p in procesos:
            print(f"  · {p.posicion}: {len(p.postulaciones)} candidatos — /postular/{p.token}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
