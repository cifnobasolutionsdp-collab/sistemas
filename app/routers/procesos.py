"""Procesos: carga de información, provisionamiento, cálculo y análisis de VaR."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from .. import consultas
from ..carga import cargar_cartera_csv
from ..database import get_db
from ..models import CargaInformacion, ResultadoRiesgo
from ..plantillas import templates
from ..riesgo.provisionamiento import calcular_provisionamiento
from ..riesgo.var import calcular_var

router = APIRouter(prefix="/procesos", tags=["procesos"])


def _guardar_resultado(db: Session, periodo: str, tipo: str, parametros: dict, resultados: dict) -> None:
    db.add(
        ResultadoRiesgo(
            periodo=periodo,
            tipo=tipo,
            parametros=json.dumps(parametros, ensure_ascii=False),
            resultados=json.dumps(resultados, ensure_ascii=False, default=str),
        )
    )
    db.commit()


@router.get("/carga")
def carga(request: Request, db: Session = Depends(get_db)):
    historial = (
        db.query(CargaInformacion).order_by(CargaInformacion.fecha.desc()).limit(20).all()
    )
    return templates.TemplateResponse(
        request, "proceso_carga.html", {"historial": historial, "resultado": None}
    )


@router.post("/carga")
async def cargar(request: Request, archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    contenido = await archivo.read()
    resultado = cargar_cartera_csv(db, contenido, archivo.filename or "cartera.csv")
    historial = (
        db.query(CargaInformacion).order_by(CargaInformacion.fecha.desc()).limit(20).all()
    )
    return templates.TemplateResponse(
        request, "proceso_carga.html", {"historial": historial, "resultado": resultado}
    )


@router.get("/provisionamiento")
def provisionamiento(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    periodos = consultas.periodos_disponibles(db)
    periodo_sel = consultas.periodo_actual(db, periodo)
    return templates.TemplateResponse(
        request,
        "proceso_provisionamiento.html",
        {"periodos": periodos, "periodo": periodo_sel, "resultado": None},
    )


@router.post("/provisionamiento")
def ejecutar_provisionamiento(request: Request, periodo: str = Form(...), db: Session = Depends(get_db)):
    resultado = calcular_provisionamiento(db, periodo)
    _guardar_resultado(db, periodo, "provisionamiento", {}, resultado)
    return templates.TemplateResponse(
        request,
        "proceso_provisionamiento.html",
        {
            "periodos": consultas.periodos_disponibles(db),
            "periodo": periodo,
            "resultado": resultado,
        },
    )


@router.get("/var")
def var_form(request: Request, periodo: str | None = None, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "proceso_var.html",
        {
            "periodos": consultas.periodos_disponibles(db),
            "periodo": consultas.periodo_actual(db, periodo),
            "resultado": None,
            "parametros": {"confianza": 99, "simulaciones": 2000, "factores": "1.0, 1.5, 2.0"},
        },
    )


@router.post("/var")
def ejecutar_var(
    request: Request,
    periodo: str = Form(...),
    confianza: float = Form(99.0),
    simulaciones: int = Form(2000),
    factores: str = Form("1.0, 1.5, 2.0"),
    db: Session = Depends(get_db),
):
    try:
        lista_factores = tuple(
            sorted({float(f.strip()) for f in factores.split(",") if f.strip()}) or (1.0,)
        )
    except ValueError:
        lista_factores = (1.0, 1.5, 2.0)
    if 1.0 not in lista_factores:
        lista_factores = (1.0, *lista_factores)
    simulaciones = max(100, min(simulaciones, 20_000))
    confianza = max(50.0, min(confianza, 99.99))

    resultado = calcular_var(
        db,
        periodo,
        confianza=confianza / 100.0,
        simulaciones=simulaciones,
        factores_estres=lista_factores,
    )
    parametros = {
        "confianza": confianza,
        "simulaciones": simulaciones,
        "factores": list(lista_factores),
    }
    resultado_sin_hist = {k: v for k, v in resultado.items() if k != "histograma"}
    _guardar_resultado(db, periodo, "var", parametros, resultado_sin_hist)
    return templates.TemplateResponse(
        request,
        "proceso_var.html",
        {
            "periodos": consultas.periodos_disponibles(db),
            "periodo": periodo,
            "resultado": resultado,
            "parametros": {
                "confianza": confianza,
                "simulaciones": simulaciones,
                "factores": ", ".join(f"{f:g}" for f in lista_factores),
            },
        },
    )


@router.get("/analisis-var")
def analisis_var(request: Request, db: Session = Depends(get_db)):
    resultados = (
        db.query(ResultadoRiesgo)
        .filter(ResultadoRiesgo.tipo == "var")
        .order_by(ResultadoRiesgo.fecha.desc())
        .limit(50)
        .all()
    )
    historico = []
    for r in resultados:
        datos = json.loads(r.resultados)
        escenario_base = next(
            (e for e in datos.get("escenarios", []) if e.get("factor") == 1.0), None
        )
        historico.append(
            {"registro": r, "datos": datos, "base": escenario_base, "parametros": json.loads(r.parametros)}
        )
    return templates.TemplateResponse(request, "analisis_var.html", {"historico": historico})


@router.get("/analisis-var/{resultado_id}")
def analisis_var_detalle(resultado_id: int, request: Request, db: Session = Depends(get_db)):
    r = db.get(ResultadoRiesgo, resultado_id)
    if r is None or r.tipo != "var":
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "analisis_var_detalle.html",
        {"registro": r, "datos": json.loads(r.resultados), "parametros": json.loads(r.parametros)},
    )
