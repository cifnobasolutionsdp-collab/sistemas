"""Mantenimiento genérico de catálogos (alta, consulta, edición y baja)."""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..catalogos_config import CATALOGOS, Catalogo, etiqueta_registro
from ..database import get_db
from ..plantillas import templates

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


def _catalogo(slug: str) -> Catalogo:
    if slug not in CATALOGOS:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    return CATALOGOS[slug]


def _opciones_fk(db: Session, cat: Catalogo) -> dict[str, list]:
    opciones = {}
    for campo in cat.campos:
        if campo.tipo == "select" and campo.fk is not None:
            registros = db.query(campo.fk).all()
            opciones[campo.nombre] = [(r.id, etiqueta_registro(r)) for r in registros]
    return opciones


def _valores_de_formulario(cat: Catalogo, formulario) -> tuple[dict, list[str]]:
    valores: dict = {}
    errores: list[str] = []
    for campo in cat.campos:
        crudo = (formulario.get(campo.nombre) or "").strip()
        if not crudo:
            if campo.requerido:
                errores.append(f"El campo «{campo.etiqueta}» es obligatorio.")
            else:
                valores[campo.nombre] = None if campo.tipo in ("number", "entero", "select") else ""
            continue
        try:
            if campo.tipo == "number":
                valores[campo.nombre] = float(crudo)
            elif campo.tipo == "entero":
                valores[campo.nombre] = int(float(crudo))
            elif campo.tipo == "select" and campo.fk is not None:
                valores[campo.nombre] = int(crudo)
            else:
                valores[campo.nombre] = crudo
        except ValueError:
            errores.append(f"El campo «{campo.etiqueta}» tiene un valor inválido.")
    return valores, errores


def _vista_lista(request: Request, db: Session, cat: Catalogo, mensaje: str = ""):
    registros = db.query(cat.modelo).order_by(cat.modelo.id).all()
    opciones = _opciones_fk(db, cat)
    return templates.TemplateResponse(
        request,
        "catalogo_lista.html",
        {
            "cat": cat,
            "registros": registros,
            "opciones_fk": opciones,
            "mapa_fk": {nombre: dict(lista) for nombre, lista in opciones.items()},
            "mensaje": mensaje,
        },
    )


@router.get("/{slug}")
def listar(slug: str, request: Request, msg: str = "", db: Session = Depends(get_db)):
    return _vista_lista(request, db, _catalogo(slug), msg)


@router.get("/{slug}/nuevo")
def nuevo(slug: str, request: Request, db: Session = Depends(get_db)):
    cat = _catalogo(slug)
    return templates.TemplateResponse(
        request,
        "catalogo_form.html",
        {"cat": cat, "registro": None, "opciones_fk": _opciones_fk(db, cat), "errores": []},
    )


@router.post("/{slug}/nuevo")
async def crear(slug: str, request: Request, db: Session = Depends(get_db)):
    cat = _catalogo(slug)
    formulario = await request.form()
    valores, errores = _valores_de_formulario(cat, formulario)
    if not errores:
        try:
            db.add(cat.modelo(**valores))
            db.commit()
            return RedirectResponse(
                f"/catalogos/{slug}?msg={quote('Registro creado correctamente.')}", status_code=303
            )
        except IntegrityError:
            db.rollback()
            errores.append("Ya existe un registro con esa clave o el valor duplica uno existente.")
    return templates.TemplateResponse(
        request,
        "catalogo_form.html",
        {"cat": cat, "registro": dict(formulario), "opciones_fk": _opciones_fk(db, cat), "errores": errores},
    )


@router.get("/{slug}/{registro_id}/editar")
def editar(slug: str, registro_id: int, request: Request, db: Session = Depends(get_db)):
    cat = _catalogo(slug)
    registro = db.get(cat.modelo, registro_id)
    if registro is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "catalogo_form.html",
        {"cat": cat, "registro": registro, "opciones_fk": _opciones_fk(db, cat), "errores": []},
    )


@router.post("/{slug}/{registro_id}/editar")
async def actualizar(slug: str, registro_id: int, request: Request, db: Session = Depends(get_db)):
    cat = _catalogo(slug)
    registro = db.get(cat.modelo, registro_id)
    if registro is None:
        raise HTTPException(status_code=404)
    formulario = await request.form()
    valores, errores = _valores_de_formulario(cat, formulario)
    if not errores:
        try:
            for nombre, valor in valores.items():
                setattr(registro, nombre, valor)
            db.commit()
            return RedirectResponse(
                f"/catalogos/{slug}?msg={quote('Registro actualizado correctamente.')}", status_code=303
            )
        except IntegrityError:
            db.rollback()
            errores.append("Ya existe un registro con esa clave o el valor duplica uno existente.")
    return templates.TemplateResponse(
        request,
        "catalogo_form.html",
        {"cat": cat, "registro": registro, "opciones_fk": _opciones_fk(db, cat), "errores": errores},
    )


@router.post("/{slug}/{registro_id}/eliminar")
def eliminar(slug: str, registro_id: int, db: Session = Depends(get_db)):
    cat = _catalogo(slug)
    registro = db.get(cat.modelo, registro_id)
    mensaje = "Registro eliminado."
    if registro is not None:
        try:
            db.delete(registro)
            db.commit()
        except IntegrityError:
            db.rollback()
            mensaje = "No se puede eliminar: el registro está referenciado por otros datos."
    return RedirectResponse(f"/catalogos/{slug}?msg={quote(mensaje)}", status_code=303)
