# Etapas de implementación

Esquema general de las etapas de implementación del sistema y cómo las
soporta este repositorio.

| # | Etapa | Soporte en el sistema |
|---|-------|-----------------------|
| 1 | Definición de información (lay out) | `docs/layout_carga.md` define el lay out oficial de alimentación. |
| 2 | Definición de la obtención del lay out | Sección «Obtención del lay out» en `docs/layout_carga.md`; el core genera el CSV al cierre mensual. |
| 3 | Obtención de la información (lay out) | `data/layout_ejemplo.csv` como referencia; `scripts/generar_layout_ejemplo.py` lo regenera. |
| 4 | Implementación de la base de datos en ambiente de pruebas | `python scripts/seed.py` crea el esquema (SQLite por omisión) y siembra catálogos y cartera de prueba. |
| 5 | Implementación del sistema en ambiente de pruebas | `uvicorn app.main:app --reload` levanta el sistema completo en pruebas. |
| 6 | Capacitación al usuario | La interfaz está en español y cada módulo incluye descripciones; el README documenta cada flujo. |
| 7 | Pruebas de carga de información | Módulo **Procesos → Carga de información** con validación renglón a renglón e historial de cargas. |
| 8 | Pruebas de funcionamiento de los módulos | Suite automatizada `pytest` (catálogos, consultas, procesos y reportes). |
| 9 | Pruebas y validación de datos | Los rechazos de carga se reportan con línea y motivo; las consultas cuadran saldos vigente/vencido contra totales. |
| 10 | Implementación de base de datos en producción | Definir `DATABASE_URL` (PostgreSQL/SQL Server) y ejecutar `scripts/seed.py --sin-cartera` para catálogos iniciales. |
| 11 | Implementación del sistema en servidor de producción | Desplegar con `uvicorn`/`gunicorn` detrás de un proxy inverso (ver README). |
| 12 | Implementación en PC de usuarios | Aplicación 100 % web: los usuarios sólo requieren un navegador apuntando al servidor. |
