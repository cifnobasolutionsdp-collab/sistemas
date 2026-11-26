#!/bin/bash
# Sistema de Evaluación y Monitoreo Financiero — doble clic para iniciar (macOS)
cd "$(dirname "$0")"
echo "============================================================"
echo "  Sistema de Evaluación y Monitoreo Financiero"
echo "============================================================"
if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python. Descárguelo de https://www.python.org/downloads/ y vuelva a abrir este archivo."
  open https://www.python.org/downloads/
  read -r -p "Presione Enter para salir..."
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "Preparando el sistema por primera vez, espere unos minutos..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt || { read -r -p "Error al instalar. Presione Enter..."; exit 1; }
  .venv/bin/python scripts/seed_monitoreo.py
fi
echo
echo "El sistema se abrirá en su navegador: http://localhost:8000/monitoreo"
echo "NO cierre esta ventana mientras use el sistema."
(sleep 3; open http://localhost:8000/monitoreo) &
.venv/bin/python -m uvicorn app.main:app --port 8000
