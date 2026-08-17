"""Gestión de procesos de reclutamiento (vacantes).

Creación de procesos (Fast Apply, estándar, desde plantilla o copiando otro
proceso), preguntas de filtro con ponderación y opciones excluyentes,
mensajes del chatbot y publicación multicanal con fechas automáticas y
póster con código QR.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..plantillas import templates
from ..plantillas_proceso import PLANTILLAS, generar_descripcion
from ..qr import qr_svg

router = APIRouter(prefix="/procesos", tags=["procesos"])


def _proceso(db: Session, proceso_id: int) -> models.Proceso:
    proceso = db.get(models.Proceso, proceso_id)
    if proceso is None:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    return proceso


def _fecha(valor: str | None) -> date | None:
    if not valor:
        return None
    return date.fromisoformat(valor)


def _catalogos_formulario(db: Session) -> dict:
    return {
        "areas": db.query(models.Area).order_by(models.Area.nombre).all(),
        "sucursales": db.query(models.Sucursal).order_by(models.Sucursal.nombre).all(),
    }


@router.get("")
def listar(request: Request, db: Session = Depends(get_db)):
    procesos = db.query(models.Proceso).order_by(models.Proceso.creado_en.desc()).all()
    return templates.TemplateResponse(request, "procesos_lista.html", {"procesos": procesos})


@router.get("/nuevo")
def nuevo(request: Request, db: Session = Depends(get_db)):
    """Alternativas de creación: plantilla, copia, estándar o Fast Apply."""
    procesos = db.query(models.Proceso).order_by(models.Proceso.creado_en.desc()).all()
    return templates.TemplateResponse(
        request,
        "proceso_nuevo.html",
        {"plantillas": PLANTILLAS, "procesos": procesos},
    )


@router.get("/crear")
def crear_formulario(
    request: Request,
    tipo: str = "fast_apply",
    plantilla: str = "",
    copiar: int | None = None,
    db: Session = Depends(get_db),
):
    datos = {"tipo": tipo if tipo in models.TIPOS_PROCESO else "fast_apply"}
    origen = None
    if plantilla and plantilla in PLANTILLAS:
        p = PLANTILLAS[plantilla]
        datos.update(
            posicion=p.posicion,
            jornada=p.jornada,
            modalidad=p.modalidad,
            descripcion=p.descripcion,
        )
        origen = f"Plantilla: {p.nombre}"
    elif copiar is not None:
        base = _proceso(db, copiar)
        datos.update(
            tipo=base.tipo,
            posicion=base.posicion,
            area_id=base.area_id,
            sucursal_id=base.sucursal_id,
            jornada=base.jornada,
            modalidad=base.modalidad,
            descripcion=base.descripcion,
            vacantes=base.vacantes,
        )
        origen = f"Copia de: {base.posicion} (#{base.id})"
    contexto = {
        "datos": datos,
        "origen": origen,
        "plantilla": plantilla,
        "copiar": copiar,
        **_catalogos_formulario(db),
    }
    return templates.TemplateResponse(request, "proceso_form.html", contexto)


@router.post("/crear")
async def crear(request: Request, db: Session = Depends(get_db)):
    formulario = await request.form()
    posicion = (formulario.get("posicion") or "").strip()
    if not posicion:
        raise HTTPException(status_code=422, detail="La posición de la oferta es obligatoria")

    area_id = int(formulario.get("area_id")) if formulario.get("area_id") else None
    sucursal_id = int(formulario.get("sucursal_id")) if formulario.get("sucursal_id") else None
    descripcion = (formulario.get("descripcion") or "").strip()
    if not descripcion and formulario.get("generar_ia"):
        area = db.get(models.Area, area_id) if area_id else None
        sucursal = db.get(models.Sucursal, sucursal_id) if sucursal_id else None
        descripcion = generar_descripcion(
            posicion,
            area.nombre if area else "",
            formulario.get("jornada") or "",
            formulario.get("modalidad") or "",
            sucursal.nombre if sucursal else "",
        )

    proceso = models.Proceso(
        tipo=formulario.get("tipo") if formulario.get("tipo") in models.TIPOS_PROCESO else "fast_apply",
        posicion=posicion,
        area_id=area_id,
        sucursal_id=sucursal_id,
        jornada=formulario.get("jornada") or "Jornada Completa",
        modalidad=formulario.get("modalidad") or "Presencial",
        descripcion=descripcion,
        vacantes=int(formulario.get("vacantes") or 1),
        salario_min=float(formulario.get("salario_min")) if formulario.get("salario_min") else None,
        salario_max=float(formulario.get("salario_max")) if formulario.get("salario_max") else None,
    )
    db.add(proceso)
    db.flush()

    # Preguntas precargadas desde la plantilla o el proceso copiado
    plantilla = formulario.get("plantilla") or ""
    copiar = formulario.get("copiar") or ""
    if plantilla in PLANTILLAS:
        for orden, pp in enumerate(PLANTILLAS[plantilla].preguntas, start=1):
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
    elif copiar:
        base = db.get(models.Proceso, int(copiar))
        if base is not None:
            for p in base.preguntas:
                pregunta = models.PreguntaFiltro(
                    proceso_id=proceso.id, orden=p.orden, texto=p.texto, tipo=p.tipo
                )
                db.add(pregunta)
                db.flush()
                for o in p.opciones:
                    db.add(
                        models.OpcionRespuesta(
                            pregunta_id=pregunta.id,
                            texto=o.texto,
                            peso=o.peso,
                            excluyente=o.excluyente,
                        )
                    )
    db.commit()
    return RedirectResponse(f"/procesos/{proceso.id}", status_code=303)


@router.get("/{proceso_id}")
def detalle(proceso_id: int, request: Request, msg: str = "", db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    postulaciones = sorted(
        proceso.postulaciones,
        key=lambda p: (p.adecuacion is None, -(p.adecuacion or 0.0)),
    )
    return templates.TemplateResponse(
        request,
        "proceso_detalle.html",
        {"proceso": proceso, "postulaciones": postulaciones, "mensaje": msg},
    )


@router.get("/{proceso_id}/editar")
def editar_formulario(proceso_id: int, request: Request, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    datos = {
        "tipo": proceso.tipo,
        "posicion": proceso.posicion,
        "area_id": proceso.area_id,
        "sucursal_id": proceso.sucursal_id,
        "jornada": proceso.jornada,
        "modalidad": proceso.modalidad,
        "descripcion": proceso.descripcion,
        "vacantes": proceso.vacantes,
        "salario_min": proceso.salario_min,
        "salario_max": proceso.salario_max,
    }
    contexto = {
        "datos": datos,
        "proceso": proceso,
        "origen": None,
        "plantilla": "",
        "copiar": None,
        **_catalogos_formulario(db),
    }
    return templates.TemplateResponse(request, "proceso_form.html", contexto)


@router.post("/{proceso_id}/editar")
async def editar(proceso_id: int, request: Request, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    formulario = await request.form()
    posicion = (formulario.get("posicion") or "").strip()
    if posicion:
        proceso.posicion = posicion
    proceso.area_id = int(formulario.get("area_id")) if formulario.get("area_id") else None
    proceso.sucursal_id = int(formulario.get("sucursal_id")) if formulario.get("sucursal_id") else None
    proceso.jornada = formulario.get("jornada") or proceso.jornada
    proceso.modalidad = formulario.get("modalidad") or proceso.modalidad
    proceso.vacantes = int(formulario.get("vacantes") or proceso.vacantes)
    proceso.salario_min = float(formulario.get("salario_min")) if formulario.get("salario_min") else None
    proceso.salario_max = float(formulario.get("salario_max")) if formulario.get("salario_max") else None
    descripcion = (formulario.get("descripcion") or "").strip()
    if not descripcion and formulario.get("generar_ia"):
        descripcion = generar_descripcion(
            proceso.posicion,
            proceso.area.nombre if proceso.area else "",
            proceso.jornada,
            proceso.modalidad,
            proceso.sucursal.nombre if proceso.sucursal else "",
        )
    proceso.descripcion = descripcion
    db.commit()
    return RedirectResponse(
        f"/procesos/{proceso.id}?msg={quote('Proceso actualizado.')}", status_code=303
    )


# ---------------------------------------------------------------------------
# Preguntas de filtro (killer questions)
# ---------------------------------------------------------------------------
@router.post("/{proceso_id}/preguntas/nueva")
def agregar_pregunta(
    proceso_id: int,
    texto: str = Form(...),
    tipo: str = Form("cerrada"),
    peso_si: float = Form(10.0),
    tratamiento_no: str = Form("sin_puntos"),
    db: Session = Depends(get_db),
):
    proceso = _proceso(db, proceso_id)
    orden = max((p.orden for p in proceso.preguntas), default=0) + 1
    pregunta = models.PreguntaFiltro(
        proceso_id=proceso.id, orden=orden, texto=texto.strip()[:300], tipo=tipo
    )
    db.add(pregunta)
    db.flush()
    if tipo == "cerrada":
        db.add(models.OpcionRespuesta(pregunta_id=pregunta.id, texto="Sí", peso=peso_si))
        db.add(
            models.OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto="No",
                peso=0.0,
                excluyente=(tratamiento_no == "excluyente"),
            )
        )
    db.commit()
    return RedirectResponse(
        f"/procesos/{proceso.id}?msg={quote('Pregunta de filtro agregada.')}#preguntas",
        status_code=303,
    )


@router.post("/{proceso_id}/preguntas/{pregunta_id}/eliminar")
def eliminar_pregunta(proceso_id: int, pregunta_id: int, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    pregunta = db.get(models.PreguntaFiltro, pregunta_id)
    if pregunta is not None and pregunta.proceso_id == proceso.id:
        db.delete(pregunta)
        db.commit()
    return RedirectResponse(
        f"/procesos/{proceso.id}?msg={quote('Pregunta eliminada.')}#preguntas", status_code=303
    )


# ---------------------------------------------------------------------------
# Mensajes del chatbot
# ---------------------------------------------------------------------------
@router.get("/{proceso_id}/mensajes")
def mensajes_formulario(proceso_id: int, request: Request, db: Session = Depends(get_db)):
    from ..chatbot import MENSAJES_POR_OMISION, mensaje_de

    proceso = _proceso(db, proceso_id)
    vista_previa = {
        campo: mensaje_de(proceso, campo, "Andrea")
        for campo in MENSAJES_POR_OMISION
    }
    return templates.TemplateResponse(
        request,
        "proceso_mensajes.html",
        {"proceso": proceso, "omision": MENSAJES_POR_OMISION, "vista_previa": vista_previa},
    )


@router.post("/{proceso_id}/mensajes")
def guardar_mensajes(
    proceso_id: int,
    msg_bienvenida: str = Form(""),
    msg_solicitud_cv: str = Form(""),
    msg_pre_cuestionario: str = Form(""),
    msg_despedida: str = Form(""),
    solicitar_cv: str = Form(""),
    db: Session = Depends(get_db),
):
    proceso = _proceso(db, proceso_id)
    proceso.msg_bienvenida = msg_bienvenida.strip()[:300]
    proceso.msg_solicitud_cv = msg_solicitud_cv.strip()[:300]
    proceso.msg_pre_cuestionario = msg_pre_cuestionario.strip()[:300]
    proceso.msg_despedida = msg_despedida.strip()[:300]
    proceso.solicitar_cv = bool(solicitar_cv)
    db.commit()
    return RedirectResponse(
        f"/procesos/{proceso.id}/mensajes", status_code=303
    )


# ---------------------------------------------------------------------------
# Publicación y difusión
# ---------------------------------------------------------------------------
@router.get("/{proceso_id}/publicacion")
def publicacion_formulario(proceso_id: int, request: Request, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    canales = db.query(models.CanalPublicacion).order_by(models.CanalPublicacion.nombre).all()
    seleccionados = {cp.canal_id for cp in proceso.canales}
    return templates.TemplateResponse(
        request,
        "proceso_publicacion.html",
        {"proceso": proceso, "canales": canales, "seleccionados": seleccionados},
    )


@router.post("/{proceso_id}/publicacion")
async def guardar_publicacion(proceso_id: int, request: Request, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    formulario = await request.form()
    proceso.fecha_publicacion = _fecha(formulario.get("fecha_publicacion"))
    proceso.fecha_fin = _fecha(formulario.get("fecha_fin"))
    proceso.cerrado = False

    elegidos = {int(v) for v in formulario.getlist("canales")}
    for cp in list(proceso.canales):
        if cp.canal_id not in elegidos:
            db.delete(cp)
    actuales = {cp.canal_id for cp in proceso.canales}
    for canal_id in elegidos - actuales:
        db.add(models.CanalProceso(proceso_id=proceso.id, canal_id=canal_id))
    db.commit()
    return RedirectResponse(f"/procesos/{proceso.id}/publicacion", status_code=303)


@router.post("/{proceso_id}/cerrar")
def cerrar(proceso_id: int, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    proceso.cerrado = True
    db.commit()
    return RedirectResponse(
        f"/procesos/{proceso.id}?msg={quote('Proceso cerrado.')}", status_code=303
    )


@router.get("/{proceso_id}/poster")
def poster(proceso_id: int, request: Request, db: Session = Depends(get_db)):
    proceso = _proceso(db, proceso_id)
    enlace = str(request.base_url).rstrip("/") + f"/postular/{proceso.token}"
    return templates.TemplateResponse(
        request,
        "proceso_poster.html",
        {"proceso": proceso, "enlace": enlace, "qr": qr_svg(enlace)},
    )
