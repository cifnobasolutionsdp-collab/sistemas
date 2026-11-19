"""Monitoreo financiero PERLAS + IFRS 9 para SOCAPS y SOFOMES."""
from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..monitoreo.estrategias import estrategias, interrelacion, plan_de_accion
from ..monitoreo.exportar import exportar_monitoreo, plantilla_balanza, plantilla_estados
from ..monitoreo.ifrs9 import parametros as params_ifrs9
from ..monitoreo.importacion import a_numero, importar_balanza, importar_estados
from ..monitoreo.indicadores import GRUPOS, INDICADORES, INDICADORES_POR_CODIGO, calcular_indicadores
from ..monitoreo.mapeo import sembrar_reglas
from ..monitoreo.modelos import TIPOS_ENTIDAD, CargaFinanciera, Entidad, EstadoFinanciero, MetaIndicador, ReglaMapeo
from ..monitoreo.rubros import RUBROS, RUBROS_POR_CLAVE
from ..plantillas import templates

router = APIRouter(prefix="/monitoreo", tags=["monitoreo"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _entidad(db: Session, entidad_id: int) -> Entidad:
    entidad = db.get(Entidad, entidad_id)
    if entidad is None:
        raise HTTPException(404, "Entidad no encontrada")
    return entidad


def _estado(entidad: Entidad, fecha: str | None) -> EstadoFinanciero | None:
    if not entidad.estados:
        return None
    if fecha:
        for e in entidad.estados:
            if e.fecha_corte.isoformat() == fecha:
                return e
        raise HTTPException(404, "No hay información para esa fecha de corte")
    return entidad.estados[-1]


def _historial(db: Session, entidad: Entidad, estado: EstadoFinanciero, n: int = 6):
    previos = [e for e in entidad.estados if e.fecha_corte <= estado.fecha_corte][-n:]
    return [(e, calcular_indicadores(db, e)) for e in previos]


def _pct(texto: str | None) -> float | None:
    """Campos de formulario capturados en porcentaje (4.5 = 4.5 %)."""
    v = a_numero(texto)
    return None if v is None else v / 100


# ------------------------------------------------------------------ entidades
@router.get("")
def inicio(request: Request, db: Session = Depends(get_db)):
    entidades = db.query(Entidad).order_by(Entidad.nombre).all()
    resumen = []
    for ent in entidades:
        estado = _estado(ent, None)
        res = calcular_indicadores(db, estado) if estado else None
        resumen.append({"entidad": ent, "estado": estado, "res": res})
    return templates.TemplateResponse(request, "monitoreo_inicio.html", {"resumen": resumen, "tipos": TIPOS_ENTIDAD})


@router.post("/entidades")
def alta_entidad(
    clave: str = Form(...), nombre: str = Form(...), tipo: str = Form("SOCAP"), nivel: str = Form(""), db: Session = Depends(get_db)
):
    if tipo not in TIPOS_ENTIDAD:
        raise HTTPException(400, "Tipo de entidad inválido")
    if db.query(Entidad).filter(Entidad.clave == clave.strip()).first():
        raise HTTPException(400, "Ya existe una entidad con esa clave")
    ent = Entidad(clave=clave.strip(), nombre=nombre.strip(), tipo=tipo, nivel=nivel.strip())
    db.add(ent)
    db.commit()
    return RedirectResponse(f"/monitoreo/carga?entidad_id={ent.id}", status_code=303)


@router.post("/entidades/{entidad_id}/eliminar")
def eliminar_entidad(entidad_id: int, db: Session = Depends(get_db)):
    db.delete(_entidad(db, entidad_id))
    db.commit()
    return RedirectResponse("/monitoreo", status_code=303)


# ------------------------------------------------------------------ carga
@router.get("/carga")
def carga(request: Request, entidad_id: int | None = None, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "monitoreo_carga.html", _contexto_carga(db, entidad_id, None))


def _contexto_carga(db, entidad_id, resultado):
    return {
        "entidades": db.query(Entidad).order_by(Entidad.nombre).all(),
        "entidad_id": entidad_id,
        "resultado": resultado,
        "historial": db.query(CargaFinanciera).order_by(CargaFinanciera.fecha.desc()).limit(25).all(),
    }


@router.post("/carga")
async def cargar(
    request: Request,
    entidad_id: int = Form(...),
    fecha_corte: date = Form(...),
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    inflacion: str = Form(""),
    tasa_mercado: str = Form(""),
    tasa_empresarial: str = Form(""),
    db: Session = Depends(get_db),
):
    entidad = _entidad(db, entidad_id)
    contenido = await archivo.read()
    nombre = archivo.filename or "archivo"
    if tipo == "balanza":
        resultado = importar_balanza(db, entidad, fecha_corte, contenido, nombre)
    else:
        resultado = importar_estados(db, entidad, fecha_corte, contenido, nombre)
    if resultado.estado_id:
        estado = db.get(EstadoFinanciero, resultado.estado_id)
        for campo, texto in (("inflacion", inflacion), ("tasa_mercado", tasa_mercado), ("tasa_empresarial", tasa_empresarial)):
            if (v := _pct(texto)) is not None:
                setattr(estado, campo, v)
        db.commit()
    ctx = _contexto_carga(db, entidad_id, resultado)
    ctx["entidad"] = entidad
    ctx["fecha_corte"] = fecha_corte
    return templates.TemplateResponse(request, "monitoreo_carga.html", ctx)


@router.get("/plantilla/estados.xlsx")
def descargar_plantilla_estados():
    return Response(plantilla_estados(), media_type=XLSX, headers={"Content-Disposition": 'attachment; filename="layout_estados_financieros.xlsx"'})


@router.get("/plantilla/balanza.xlsx")
def descargar_plantilla_balanza():
    return Response(plantilla_balanza(), media_type=XLSX, headers={"Content-Disposition": 'attachment; filename="layout_balanza_comprobacion.xlsx"'})


# ------------------------------------------------------------------ tablero
@router.get("/entidades/{entidad_id}")
def tablero(request: Request, entidad_id: int, fecha: str | None = None, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    estado = _estado(entidad, fecha)
    if estado is None:
        return RedirectResponse(f"/monitoreo/carga?entidad_id={entidad.id}", status_code=303)
    historial = _historial(db, entidad, estado)
    res = historial[-1][1]
    return templates.TemplateResponse(
        request,
        "monitoreo_tablero.html",
        {"entidad": entidad, "estado": estado, "res": res, "historial": historial, "grupos": GRUPOS, "plan": plan_de_accion(res)},
    )


@router.post("/entidades/{entidad_id}/parametros")
def guardar_parametros(
    entidad_id: int,
    fecha: str = Form(...),
    inflacion: str = Form(""),
    tasa_mercado: str = Form(""),
    tasa_empresarial: str = Form(""),
    db: Session = Depends(get_db),
):
    estado = _estado(_entidad(db, entidad_id), fecha)
    estado.inflacion = _pct(inflacion)
    estado.tasa_mercado = _pct(tasa_mercado)
    estado.tasa_empresarial = _pct(tasa_empresarial)
    db.commit()
    return RedirectResponse(f"/monitoreo/entidades/{entidad_id}?fecha={fecha}", status_code=303)


@router.post("/entidades/{entidad_id}/periodos/eliminar")
def eliminar_periodo(entidad_id: int, fecha: str = Form(...), db: Session = Depends(get_db)):
    estado = _estado(_entidad(db, entidad_id), fecha)
    db.delete(estado)
    db.commit()
    return RedirectResponse(f"/monitoreo/entidades/{entidad_id}", status_code=303)


@router.get("/entidades/{entidad_id}/indicador/{codigo}")
def detalle_indicador(request: Request, entidad_id: int, codigo: str, fecha: str | None = None, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    if codigo not in INDICADORES_POR_CODIGO:
        raise HTTPException(404, "Indicador no encontrado")
    estado = _estado(entidad, fecha)
    if estado is None:
        raise HTTPException(404, "La entidad no tiene información cargada")
    historial = _historial(db, entidad, estado, 12)
    res = historial[-1][1]
    rel = interrelacion(codigo)
    return templates.TemplateResponse(
        request,
        "monitoreo_indicador.html",
        {
            "entidad": entidad, "estado": estado, "res": res, "fila": res["por_codigo"][codigo], "historial": historial,
            "rel": rel, "estrategias": estrategias(codigo), "codigo": codigo,
        },
    )


@router.get("/entidades/{entidad_id}/plan")
def plan(request: Request, entidad_id: int, fecha: str | None = None, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    estado = _estado(entidad, fecha)
    if estado is None:
        raise HTTPException(404, "La entidad no tiene información cargada")
    res = calcular_indicadores(db, estado)
    return templates.TemplateResponse(
        request, "monitoreo_plan.html", {"entidad": entidad, "estado": estado, "res": res, "plan": plan_de_accion(res)}
    )


@router.get("/entidades/{entidad_id}/excel")
def excel(entidad_id: int, fecha: str | None = None, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    estado = _estado(entidad, fecha)
    if estado is None:
        raise HTTPException(404, "La entidad no tiene información cargada")
    contenido = exportar_monitoreo(entidad, _historial(db, entidad, estado))
    nombre = f"monitoreo_{entidad.clave}_{estado.fecha_corte.isoformat()}.xlsx"
    return Response(contenido, media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


@router.get("/entidades/{entidad_id}/rubros")
def rubros_entidad(request: Request, entidad_id: int, fecha: str | None = None, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    estado = _estado(entidad, fecha)
    if estado is None:
        raise HTTPException(404, "La entidad no tiene información cargada")
    res = calcular_indicadores(db, estado)
    return templates.TemplateResponse(
        request, "monitoreo_rubros.html", {"entidad": entidad, "estado": estado, "datos": estado.datos(), "rubros": RUBROS, "ag": res["agregados"]}
    )


# ------------------------------------------------------------------ IFRS 9
@router.get("/entidades/{entidad_id}/ifrs9")
def ifrs9_form(request: Request, entidad_id: int, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    return templates.TemplateResponse(request, "monitoreo_ifrs9.html", {"entidad": entidad, "p": params_ifrs9(entidad.params_ifrs9())})


@router.post("/entidades/{entidad_id}/ifrs9")
async def ifrs9_guardar(request: Request, entidad_id: int, db: Session = Depends(get_db)):
    entidad = _entidad(db, entidad_id)
    form = await request.form()
    p = {}
    for k in ("pd_etapa1", "pd_etapa2", "pd_etapa3", "lgd"):
        if (v := _pct(form.get(k))) is not None:
            p[k] = max(0.0, min(1.0, v))
    escenarios = []
    for i in range(3):
        nombre = (form.get(f"esc_nombre_{i}") or "").strip()
        peso, factor = _pct(form.get(f"esc_peso_{i}")), a_numero(form.get(f"esc_factor_{i}"))
        if nombre and peso is not None and factor is not None:
            escenarios.append({"nombre": nombre, "peso": peso, "factor": factor})
    if escenarios:
        p["escenarios"] = escenarios
    entidad.parametros_ifrs9 = json.dumps(p) if form.get("accion") != "restablecer" else "{}"
    db.commit()
    return RedirectResponse(f"/monitoreo/entidades/{entidad_id}#ifrs9", status_code=303)


# ------------------------------------------------------------------ metas
@router.get("/metas")
def metas(request: Request, tipo: str = "SOCAP", db: Session = Depends(get_db)):
    if tipo not in TIPOS_ENTIDAD:
        tipo = "SOCAP"
    personalizadas = {m.codigo: m for m in db.query(MetaIndicador).filter(MetaIndicador.tipo_entidad == tipo).all()}
    filas = [
        {"ind": i, "omision": i.limites.get(tipo, (None, None)), "personal": personalizadas.get(i.codigo)}
        for i in INDICADORES
        if tipo in i.aplica and i.tipo in ("min", "max", "rango") and not i.limites_dinamicos
    ]
    return templates.TemplateResponse(request, "monitoreo_metas.html", {"filas": filas, "tipo": tipo, "tipos": TIPOS_ENTIDAD})


@router.post("/metas")
async def guardar_metas(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    tipo = form.get("tipo", "SOCAP")
    for ind in INDICADORES:
        if f"min_{ind.codigo}" not in form:
            continue
        minimo, maximo = _pct(form.get(f"min_{ind.codigo}")), _pct(form.get(f"max_{ind.codigo}"))
        if ind.formato == "veces":
            minimo, maximo = a_numero(form.get(f"min_{ind.codigo}")), a_numero(form.get(f"max_{ind.codigo}"))
        meta = db.query(MetaIndicador).filter_by(codigo=ind.codigo, tipo_entidad=tipo).one_or_none()
        if minimo is None and maximo is None:
            if meta:
                db.delete(meta)
            continue
        if meta is None:
            meta = MetaIndicador(codigo=ind.codigo, tipo_entidad=tipo)
            db.add(meta)
        meta.minimo, meta.maximo = minimo, maximo
    db.commit()
    return RedirectResponse(f"/monitoreo/metas?tipo={tipo}", status_code=303)


# ------------------------------------------------------------------ mapeo
@router.get("/mapeo")
def mapeo(request: Request, entidad_id: int | None = None, db: Session = Depends(get_db)):
    sembrar_reglas(db)
    q = db.query(ReglaMapeo)
    q = q.filter(ReglaMapeo.entidad_id == entidad_id) if entidad_id else q.filter(ReglaMapeo.entidad_id.is_(None))
    return templates.TemplateResponse(
        request,
        "monitoreo_mapeo.html",
        {
            "reglas": q.order_by(ReglaMapeo.prefijo).all(),
            "entidades": db.query(Entidad).order_by(Entidad.nombre).all(),
            "entidad_id": entidad_id,
            "rubros": [r for r in RUBROS if r.estado != "complementario"],
            "rubros_por_clave": RUBROS_POR_CLAVE,
        },
    )


@router.post("/mapeo")
def alta_regla(
    prefijo: str = Form(...), rubro: str = Form(...), descripcion: str = Form(""), entidad_id: str = Form(""), db: Session = Depends(get_db)
):
    if rubro not in RUBROS_POR_CLAVE:
        raise HTTPException(400, "Rubro inválido")
    ent = int(entidad_id) if entidad_id else None
    regla = db.query(ReglaMapeo).filter_by(entidad_id=ent, prefijo=prefijo.strip()).one_or_none()
    if regla is None:
        regla = ReglaMapeo(entidad_id=ent, prefijo=prefijo.strip())
        db.add(regla)
    regla.rubro, regla.descripcion = rubro, descripcion.strip()
    db.commit()
    return RedirectResponse(f"/monitoreo/mapeo{'?entidad_id=' + str(ent) if ent else ''}", status_code=303)


@router.post("/mapeo/{regla_id}/eliminar")
def eliminar_regla(regla_id: int, db: Session = Depends(get_db)):
    regla = db.get(ReglaMapeo, regla_id)
    if regla is None:
        raise HTTPException(404, "Regla no encontrada")
    ent = regla.entidad_id
    db.delete(regla)
    db.commit()
    return RedirectResponse(f"/monitoreo/mapeo{'?entidad_id=' + str(ent) if ent else ''}", status_code=303)
