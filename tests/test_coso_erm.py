"""Consistencia del banco COSO ERM 2026 y del HTML autocontenido generado."""
import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "coso_erm"
BANCO = json.loads((RAIZ / "datos" / "banco_coso_erm_2026.json").read_text(encoding="utf-8"))


def _construir():
    spec = importlib.util.spec_from_file_location("construir", RAIZ / "herramientas" / "construir.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_veinte_principios_en_orden():
    numeros = [p["n"] for c in BANCO["components"] for p in c["principles"]]
    assert sorted(numeros) == list(range(1, 21))
    for c in BANCO["components"]:
        ns = [p["n"] for p in c["principles"]]
        assert ns == sorted(ns)


def test_ids_unicos_y_coherentes_con_principio():
    ids = []
    for ci, c in enumerate(BANCO["components"], start=1):
        for p in c["principles"]:
            assert p["q"], f"Principio {p['n']} sin puntos de interés"
            for k, q in enumerate(p["q"], start=1):
                assert q["id"] == f"{ci}.{p['n']}.{k}"
                assert q["t"].strip()
                ids.append(q["id"])
    assert len(ids) == len(set(ids)) == 200


def test_ponderaciones_suman_uno():
    assert abs(sum(c["peso"] for c in BANCO["components"]) - 1) < 1e-9


def test_demo_apunta_a_preguntas_existentes():
    ids = {q["id"] for c in BANCO["components"] for p in c["principles"] for q in p["q"]}
    assert set(BANCO["demo"]) <= ids


def test_banco_generado_esta_actualizado():
    assert _construir().construir_banco() == BANCO


def test_html_generado_sin_marcas_pendientes():
    html = (RAIZ / "SECI_COSO_ERM_2026.html").read_text(encoding="utf-8")
    for marca in ("/*__CSS__*/", "/*__JS__*/", "/*__BANCO__*/"):
        assert marca not in html
    assert f'"version":"{BANCO["version"]}"' in html
    # El HTML debe incluir la versión vigente de cada módulo fuente.
    for modulo in _construir().MODULOS_JS:
        fuente = (RAIZ / "src" / modulo).read_text(encoding="utf-8")
        assert fuente in html, f"{modulo} cambió: ejecute coso_erm/herramientas/construir.py"
