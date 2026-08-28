"""Motor conversacional Fast Apply.

Implementa la conversación guiada con el candidato: bienvenida, solicitud
opcional de currículum, cuestionario de preguntas de filtro con avance o
descarte automático (opciones excluyentes), cálculo del nivel de adecuación
y generación automática del CV a partir de la conversación.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from . import models

NOMBRE_ASISTENTE = "Fina"
NOMBRE_EMPRESA = "tu institución financiera"

MENSAJES_POR_OMISION = {
    "msg_bienvenida": (
        "¡Hola, {{nombre}}! Soy "
        + NOMBRE_ASISTENTE
        + ", tu asistente virtual de {{empresa}} y estoy aquí para ayudarte en el "
        "proceso de aplicación a la oferta de {{posicion}}."
    ),
    "msg_solicitud_cv": (
        "¿Quieres compartir un resumen de tu experiencia para completar aún más tu "
        "perfil, o prefieres continuar sin hacerlo? No es obligatorio, pero puede "
        "ayudarte a destacar. Si decides no compartirlo, no hay ningún problema."
    ),
    "msg_pre_cuestionario": (
        "¡Perfecto! Ahora vamos a comenzar con las preguntas para tu aplicación a "
        "la oferta. Comencemos."
    ),
    "msg_despedida": (
        "¡Gracias, {{nombre}}! Registramos tu postulación y generamos tu CV "
        "automáticamente. El equipo de reclutamiento de {{empresa}} revisará tu "
        "perfil y te contactará muy pronto."
    ),
}

MENSAJE_DESCARTE = (
    "Gracias por tu interés, {{nombre}}. Por el momento tu perfil no cumple con un "
    "requisito indispensable de la vacante, por lo que no podremos continuar con "
    "esta aplicación. ¡Te invitamos a postularte a nuestras próximas vacantes!"
)


def mensaje_de(proceso: models.Proceso, campo: str, nombre: str = "") -> str:
    """Mensaje configurado del proceso (o el de omisión) con variables resueltas."""
    texto = getattr(proceso, campo, "") or MENSAJES_POR_OMISION.get(campo, "")
    empresa = proceso.sucursal.nombre if proceso.sucursal else NOMBRE_EMPRESA
    return (
        texto.replace("{{nombre}}", nombre or "candidato")
        .replace("{{empresa}}", empresa)
        .replace("{{posicion}}", proceso.posicion)
    )


def _bot(db: Session, postulacion: models.Postulacion, texto: str) -> None:
    db.add(models.MensajeChat(postulacion_id=postulacion.id, emisor="bot", texto=texto))


def _candidato(db: Session, postulacion: models.Postulacion, texto: str) -> None:
    db.add(models.MensajeChat(postulacion_id=postulacion.id, emisor="candidato", texto=texto))


def iniciar_postulacion(
    db: Session,
    proceso: models.Proceso,
    nombre: str,
    telefono: str = "",
    correo: str = "",
) -> models.Postulacion:
    """Registra al candidato y arranca la conversación."""
    postulacion = models.Postulacion(
        proceso_id=proceso.id,
        nombre=nombre.strip(),
        telefono=telefono.strip(),
        correo=correo.strip(),
    )
    db.add(postulacion)
    db.flush()

    _candidato(db, postulacion, f"Hola, soy {postulacion.nombre}. Me interesa la vacante.")
    _bot(db, postulacion, mensaje_de(proceso, "msg_bienvenida", postulacion.nombre))

    if proceso.solicitar_cv:
        postulacion.paso = "cv"
        _bot(db, postulacion, mensaje_de(proceso, "msg_solicitud_cv", postulacion.nombre))
    else:
        _avanzar_a_cuestionario(db, postulacion)
    db.commit()
    db.refresh(postulacion)
    return postulacion


def _avanzar_a_cuestionario(db: Session, postulacion: models.Postulacion) -> None:
    proceso = postulacion.proceso
    if proceso.preguntas:
        _bot(db, postulacion, mensaje_de(proceso, "msg_pre_cuestionario", postulacion.nombre))
        postulacion.paso = "cuestionario:0"
        _bot(db, postulacion, proceso.preguntas[0].texto)
    else:
        # Sin preguntas de filtro el proceso sigue funcionando: el candidato
        # se postula sin filtros automáticos en la conversación.
        _finalizar(db, postulacion)


def registrar_cv(db: Session, postulacion: models.Postulacion, resumen: str) -> None:
    """Registra (o no) el resumen de experiencia y continúa la conversación."""
    resumen = resumen.strip()
    if resumen:
        postulacion.resumen_cv = resumen
        _candidato(db, postulacion, resumen)
    else:
        _candidato(db, postulacion, "Prefiero continuar sin compartir mi experiencia.")
    _avanzar_a_cuestionario(db, postulacion)
    db.commit()


def pregunta_actual(postulacion: models.Postulacion) -> models.PreguntaFiltro | None:
    if not postulacion.paso.startswith("cuestionario:"):
        return None
    indice = int(postulacion.paso.split(":")[1])
    preguntas = postulacion.proceso.preguntas
    return preguntas[indice] if indice < len(preguntas) else None


def responder_pregunta(
    db: Session,
    postulacion: models.Postulacion,
    opcion_id: int | None = None,
    texto: str = "",
) -> None:
    """Registra la respuesta a la pregunta en curso y avanza o descarta."""
    pregunta = pregunta_actual(postulacion)
    if pregunta is None:
        return

    opcion = None
    if pregunta.tipo == "cerrada":
        opcion = next((o for o in pregunta.opciones if o.id == opcion_id), None)
        if opcion is None:
            return
        _candidato(db, postulacion, opcion.texto)
        postulacion.puntaje += 0.0 if opcion.excluyente else opcion.peso
    else:
        texto = texto.strip()
        if not texto:
            return
        _candidato(db, postulacion, texto)

    db.add(
        models.RespuestaCandidato(
            postulacion_id=postulacion.id,
            pregunta_id=pregunta.id,
            opcion_id=opcion.id if opcion else None,
            texto=texto if pregunta.tipo == "abierta" else (opcion.texto if opcion else ""),
        )
    )

    if opcion is not None and opcion.excluyente:
        _descartar(db, postulacion)
        db.commit()
        return

    indice = int(postulacion.paso.split(":")[1]) + 1
    preguntas = postulacion.proceso.preguntas
    if indice < len(preguntas):
        postulacion.paso = f"cuestionario:{indice}"
        _bot(db, postulacion, preguntas[indice].texto)
    else:
        _finalizar(db, postulacion)
    db.commit()


def calcular_adecuacion(postulacion: models.Postulacion) -> float | None:
    """Nivel de adecuación: puntaje obtenido entre el máximo posible (%)."""
    maximo = sum(p.peso_maximo for p in postulacion.proceso.preguntas)
    if maximo <= 0:
        return None
    return round(100.0 * postulacion.puntaje / maximo, 1)


def _finalizar(db: Session, postulacion: models.Postulacion) -> None:
    postulacion.estado = "postulado"
    postulacion.paso = "fin"
    postulacion.completada_en = datetime.utcnow()
    postulacion.adecuacion = calcular_adecuacion(postulacion)
    _bot(db, postulacion, mensaje_de(postulacion.proceso, "msg_despedida", postulacion.nombre))


def _descartar(db: Session, postulacion: models.Postulacion) -> None:
    postulacion.estado = "descartado"
    postulacion.paso = "fin"
    postulacion.completada_en = datetime.utcnow()
    postulacion.adecuacion = calcular_adecuacion(postulacion)
    _bot(db, postulacion, MENSAJE_DESCARTE.replace("{{nombre}}", postulacion.nombre))


def generar_cv(postulacion: models.Postulacion) -> dict:
    """CV autogenerado a partir de la información de la conversación."""
    proceso = postulacion.proceso
    respuestas = []
    for r in postulacion.respuestas:
        respuestas.append(
            {
                "pregunta": r.pregunta.texto,
                "respuesta": r.texto or (r.opcion.texto if r.opcion else ""),
                "peso": (None if r.opcion is None or r.opcion.excluyente else r.opcion.peso),
                "excluyente": bool(r.opcion and r.opcion.excluyente),
            }
        )
    return {
        "nombre": postulacion.nombre,
        "telefono": postulacion.telefono,
        "correo": postulacion.correo,
        "posicion": proceso.posicion,
        "resumen": postulacion.resumen_cv,
        "respuestas": respuestas,
        "adecuacion": postulacion.adecuacion,
        "fecha": postulacion.completada_en or postulacion.iniciada_en,
    }
