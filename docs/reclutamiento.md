# Sistema de Reclutamiento y Selección — SOCAPS / SOFIPOS / SOFOMES

Aplicación web de atracción de talento con **postulación conversacional
exprés («Fast Apply»)**, orientada a instituciones del sector financiero
popular mexicano: Sociedades Cooperativas de Ahorro y Préstamo (SOCAPS),
Sociedades Financieras Populares (SOFIPOS) y Sociedades Financieras de
Objeto Múltiple (SOFOMES).

## Ejecución

```bash
pip install -r requirements.txt
python scripts/seed_reclutamiento.py        # datos de demostración (opcional)
uvicorn reclutamiento.main:app --reload --port 8001
```

La base de datos por omisión es SQLite (`reclutamiento.db`); puede
cambiarse con la variable de entorno `RECLUTAMIENTO_DATABASE_URL`.

## Módulos

### 1. Procesos de reclutamiento (vacantes)

Alternativas de creación (menú **Procesos → Crear proceso**):

- **Proceso Fast Apply** — postulación conversacional exprés.
- **Proceso estándar** — gestión tradicional de la vacante.
- **Usar una plantilla** — puestos precargados del sector financiero, con
  descripción y preguntas de filtro incluidas: Asesor de Crédito, Cajero /
  Ejecutivo de Ventanilla, Gerente de Sucursal, Analista de Crédito y
  Riesgos, y Promotor de Captación y Ahorro.
- **Copiar de otro proceso** — duplica datos y preguntas de un proceso
  existente con un nuevo enlace de postulación.

Cada proceso registra posición, área, sucursal, jornada, modalidad,
número de vacantes, rango salarial y descripción. Si la descripción se
deja vacía, el **asistente de redacción (IA)** puede generarla a partir
de los datos de la vacante.

### 2. Preguntas de filtro (Killer Questions)

Preguntas que el chatbot envía durante la conversación para avanzar o
descartar candidatos automáticamente:

- **Cerradas (Sí / No)** con **peso** por respuesta; el «No» puede
  configurarse como **excluyente** (descarta al candidato en el momento).
- **Abiertas** de respuesta libre (se integran al CV autogenerado).
- Si el proceso no tiene preguntas, sigue funcionando sin filtros
  automáticos.

El **nivel de adecuación** del candidato se calcula como el puntaje
obtenido entre el máximo posible del cuestionario (por ejemplo, 97%).

### 3. Mensajes del chatbot

Los mensajes de la conversación son personalizables por proceso (máximo
300 caracteres cada uno) con variables `{{nombre}}`, `{{empresa}}` y
`{{posicion}}`: bienvenida, solicitud opcional de currículum, mensaje
previo al cuestionario y despedida. La pantalla incluye una **vista
previa en un entorno de mensajería** con las preguntas configuradas.

### 4. Postulación del candidato (experiencia Fast Apply)

Enlace público `/postular/{token}` con conversación guiada estilo
mensajería instantánea:

1. Registro simple (nombre y contacto), sin formularios largos.
2. Solicitud opcional del resumen de experiencia (currículum).
3. Cuestionario pregunta por pregunta con botones de respuesta.
4. Descarte automático inmediato al responder una opción excluyente.
5. **CV autogenerado** al instante con los datos de la conversación,
   listo para gestionar e imprimir desde el panel del reclutador.

### 5. Publicación y difusión

- Selección de **canales**: portales de empleo (Computrabajo, OCC,
  Google for Jobs), micrositio propio, redes sociales, divulgación por
  correo y reclutamiento interno (catálogo configurable).
- **Publicación y desactivación automáticas** según las fechas de inicio
  y fin de aplicaciones.
- **Póster con código QR** del proceso para colocar en sucursales y
  espacios físicos como punto de atracción de talento.

### 6. Gestión de candidatos

Listado global y por proceso con nivel de adecuación, rapidez de
postulación (minutos), transcripción completa de la conversación, CV
autogenerado y cambio de estatus: **Postulado → Preseleccionado /
Descartado / Contratado**.

### 7. Tablero de indicadores

Procesos publicados, postulaciones, preseleccionados, contratados,
adecuación promedio y minutos promedio por postulación.

## Estructura

```
reclutamiento/
├── main.py               # aplicación FastAPI y tablero
├── database.py           # SQLite / RECLUTAMIENTO_DATABASE_URL
├── models.py             # procesos, preguntas, postulaciones, mensajes
├── chatbot.py            # motor conversacional, adecuación y CV
├── plantillas_proceso.py # plantillas de puestos financieros + redactor IA
├── qr.py                 # códigos QR (segno) para pósters
├── catalogos_config.py   # sucursales, áreas y canales (declarativo)
├── routers/              # procesos, candidatos, postulación, catálogos
├── templates/            # vistas Jinja2 (panel y chat del candidato)
└── static/style.css
```

Las pruebas viven en `tests/test_reclutamiento.py` y cubren el flujo
completo de postulación (adecuación al 100%, descarte por excluyente,
copia de procesos, mensajes personalizados y vacantes sin publicar).
