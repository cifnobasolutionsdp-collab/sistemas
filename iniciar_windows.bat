@echo off
chcp 65001 >nul
title Sistema de Evaluacion y Monitoreo Financiero
cd /d "%~dp0"
echo ============================================================
echo   Sistema de Evaluacion y Monitoreo Financiero
echo ============================================================
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo No se encontro Python en esta computadora.
  echo 1. Descarguelo de https://www.python.org/downloads/
  echo 2. Al instalar, marque la casilla "Add Python to PATH".
  echo 3. Vuelva a abrir este archivo.
  echo.
  start https://www.python.org/downloads/
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Preparando el sistema por primera vez, espere unos minutos...
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo No se pudieron instalar los componentes. Revise su conexion a internet.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" scripts\seed_monitoreo.py
)
echo.
echo El sistema se abrira en su navegador: http://localhost:8000/monitoreo
echo NO cierre esta ventana mientras use el sistema.
echo.
start "" http://localhost:8000/monitoreo
".venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000
pause
