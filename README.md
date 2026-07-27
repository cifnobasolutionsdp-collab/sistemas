# Sistema de Administración de Riesgos de Crédito — SOCAPS / SOFOMES

Sistema web orientado a **Sociedades Cooperativas de Ahorro y Préstamo
(SOCAPS)** y **SOFOMES**, para apoyar el cumplimiento de las normas y
requerimientos en materia de **Administración de Riesgos de Crédito** de la
Ley de Instituciones de Crédito, la **LRASCAP** y las disposiciones de la
**CNBV**.

> Los parámetros de riesgo sembrados (probabilidades de incumplimiento,
> severidades y porcentajes de reserva) son valores de referencia
> **parametrizables desde los catálogos**; deben ajustarse a la disposición
> vigente aplicable a cada entidad.

## Módulos

### 1. Mantenimiento y Consultas de Catálogos
Alta, consulta, edición y baja de:

- Producto de Crédito · Sucursales · Plazas · Regiones · Monedas
- Tipo de Cartera · Localidad · Actividades (con sector económico)
- Definición de Garantías (con % de cobertura)
- Calificaciones de Crédito (rangos de días de mora, **Probabilidad de
  Incumplimiento** y severidad)
- Reservas Preventivas (% de reserva por calificación)
- Límites (individuales y generales)

### 2. Consultas
Todas incluyen **Saldo Vigente y Saldo Vencido**:

- Préstamos otorgados por plazo
- Préstamos otorgados por monto
- Evolución histórica de la cartera (por periodo, con IMOR)
- Distribución de la cartera por: producto, sucursal, plaza, sector
  económico y región
- Seguimiento de límites individuales y generales (posición actual, uso del
  límite y estatus Cumple / Cercano / Excedido)

### 3. Procesos
- **Carga de información**: importación del lay out CSV
  (`docs/layout_carga.md`) con validación renglón a renglón, rechazos
  reportados e historial de cargas. La recarga es idempotente.
- **Cálculo de Provisionamiento de cartera**: califica cada crédito por días
  de mora y aplica el % de reserva preventiva; reporta desglose por
  calificación, reserva total, reserva/cartera e ICOR.
- **Cálculo de VaR**: simulación Monte Carlo por incumplimiento con
  **pérdida esperada, pérdida no esperada, VaR** al nivel de confianza
  elegido, **escenarios de estrés** (multiplicadores de PI) e **índice de
  concentración Herfindahl-Hirschman** (por acreditado y por dimensión).
- **Análisis de VaR**: histórico de cálculos con su detalle completo.

### 4. Reportes
- **Reporte Ejecutivo**: indicadores generales, provisionamiento, VaR,
  calificación de la cartera y principales concentraciones (imprimible/PDF).
- **Reporte de distribución de la cartera**: todas las dimensiones en un
  solo reporte imprimible.
- **Reportes personalizados**: dimensión, periodo, orden y número de
  renglones a elección, con **exportación a CSV**.

## Tecnología

- Python 3.10+ · FastAPI · SQLAlchemy 2 · Jinja2
- Base de datos: SQLite por omisión; configurable vía `DATABASE_URL`
  (PostgreSQL, SQL Server, etc.) para producción.
- Interfaz 100 % web en español; los usuarios sólo necesitan un navegador.

## Instalación y arranque (ambiente de pruebas)

```bash
pip install -r requirements.txt

# Crear esquema y sembrar catálogos + cartera de demostración (6 periodos)
python scripts/seed.py

# Levantar el sistema
uvicorn app.main:app --reload
```

Abrir <http://localhost:8000>. Para sembrar sólo catálogos (sin cartera de
demostración): `python scripts/seed.py --sin-cartera`.

Archivo de ejemplo del lay out: `data/layout_ejemplo.csv` (se regenera con
`python scripts/generar_layout_ejemplo.py`); cárguelo desde
**Procesos → Carga de información** para probar el flujo completo.

## Pruebas

```bash
pytest
```

Cubren: clasificación por mora, provisionamiento, pérdida esperada y
escenarios de estrés del VaR (con reproducibilidad por semilla), índice de
concentración, validación de la carga CSV y pruebas de humo de todas las
rutas de la aplicación.

## Producción

1. Definir `DATABASE_URL` hacia la base de producción y ejecutar
   `python scripts/seed.py --sin-cartera` para los catálogos iniciales.
2. Desplegar con un servidor ASGI, por ejemplo:
   `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
   detrás de un proxy inverso (nginx/IIS) con TLS.
3. Integrar la autenticación corporativa de la entidad (el sistema no
   incluye control de acceso; debe protegerse a nivel de red o proxy antes
   de exponerse a usuarios finales).

## Etapas de implementación

El plan de etapas (definición del lay out, ambientes de prueba y producción,
capacitación y validaciones) está documentado en
`docs/etapas_implementacion.md`.
