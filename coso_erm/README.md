# SECI · Evaluación de Control Interno COSO ERM 2026

Sistema web **de un solo archivo** (`SECI_COSO_ERM_2026.html`) que digitaliza
la herramienta de Excel «Eval COSO ERM 2026». Funciona **sin servidor y sin
internet**: basta con abrir el archivo en Chrome, Edge o Firefox. La
información se guarda en el propio equipo y se puede respaldar y restaurar.

## Uso rápido

1. Copie `SECI_COSO_ERM_2026.html` a una carpeta del equipo (o de red) y ábralo
   con doble clic.
2. En la **configuración inicial** capture la institución y la cuenta de
   **Sistemas**. Opcionalmente se crean las cuentas `auditor`, `contralor` y
   `riesgos` con contraseñas temporales (se muestran una sola vez y deben
   cambiarse en el primer acceso).
3. El Contralor interno responde el cuestionario; el Auditor interno lo valida
   y lo cierra; el Administrador de riesgos vincula la matriz de riesgos y los
   KRI; Sistemas administra usuarios y respaldos.

> Cada navegador y cada equipo tienen su propio almacenamiento. Para trabajar
> en otro equipo, descargue un respaldo y restáurelo allí.

## Perfiles

| Perfil | Puede |
|---|---|
| **Contralor interno** | Responder la evaluación (atributos a–h), evidencias, deficiencias y planes de solución; datos generales; mesa de control y lista de verificación; cargar cartera; registrar hallazgos. |
| **Auditor interno** | Validar u observar cada respuesta; registrar, dar seguimiento y cerrar hallazgos; plan anual de auditoría; enviar a revisión, devolver, cerrar y reabrir evaluaciones. |
| **Administrador de riesgos** | Matriz de riesgos (inherente/residual) vinculada a puntos de interés COSO, mapa de calor, apetito y KRI; cargar cartera. |
| **Sistemas** | Usuarios (alta, baja, perfil, restablecer contraseña, desbloqueo), respaldos, autoguardado, bitácora, configuración y conectores REST. |

Todos los perfiles consultan tablero, resultados y reportes.

## Módulos

- **Tablero**: madurez ponderada, avance, inconsistencias, planes, hallazgos,
  riesgos, KRI y pendientes del perfil que inició sesión.
- **Evaluaciones y datos generales** (hoja *Datos_Basicos*): una evaluación por
  ejercicio; se puede copiar la anterior para medir la mejora.
- **Cuestionario** (hojas *GC, EST, DES, REV, ICR*): 200 puntos de interés en
  los 20 principios de COSO ERM, con filtros (sin contestar, inconsistencias,
  riesgo alto, por validar, temas y nuevos 2026).
- **Resultados** (hojas *Resultados, Resumen, Gráfico*): puntaje y madurez por
  componente y principio, presente/funcionando, integración de componentes,
  riesgo de los puntos de interés, comparativo entre años y conclusiones.
- **Planes de solución**: deficiencias y planes con estado (pendiente, en
  proceso, vencido, concluido).
- **Auditoría interna**: hallazgos (condición, criterio, causa, efecto,
  recomendación, seguimiento), plan anual basado en riesgos y validación.
- **Contraloría de crédito y mesa de control**: revisión de expedientes con
  lista de verificación (requisitos críticos detienen la disposición),
  indicadores de excepciones y análisis de cartera (IMOR, concentración,
  antigüedad de mora, producto y sucursal).
- **Gestión de riesgos**: matriz, mapa de calor 5×5, apetito/tolerancia/
  capacidad y KRI con cálculo automático desde la cartera, la mesa de control,
  los planes y los hallazgos.
- **Reportes** imprimibles / PDF: informe ejecutivo con firmas, cédula
  detallada, planes, hallazgos, perfil de riesgos y crédito.
- **Catálogos**: criterios, madurez, normativa (editable), glosario,
  responsables y bitácora de actualizaciones 2026.

## Cálculo

- Nivel de cada punto de interés (0–5) según la hoja *Criterios*: los
  atributos son acumulativos (a Existe, b Diseñada, c Aprobado, d Difundido,
  e Implementado, f Responsable, g Funcionamiento, h Mejora continua). Nivel 1
  requiere a–b; 2 a–d; 3 a–e; 4 a–g; 5 a–h. Si se marca un atributo después de
  uno faltante, se reporta como **error en la evaluación**.
- Presente: a+b+c+d ≥ 3. Funcionando: e+f+g+h ≥ 3.
- Riesgo del punto: suma de atributos > 6 bajo, 5–6 moderado, ≤ 4 alto.
- Principio = promedio de sus puntos contestados; componente = promedio de sus
  principios; SCI = promedio ponderado (25 % GC, 20 % EST, 15 % DES, 15 % REV,
  25 % ICR, configurable).
- Madurez: 0–0.99 Inexistente · 1–1.99 Inicial · 2–2.99 Repetible ·
  3–3.99 Definido · 4–4.99 Gestionado · 5 Optimizado.

## Actualizaciones al contenido del Excel

Se listan también dentro del sistema (*Catálogos → Actualizaciones 2026*):

- Se corrigió la estructura de Estrategia: el Principio 8 (estrategias
  alternativas) tenía las preguntas de IA y el Principio 9 (objetivos de
  negocio) las de estrategias alternativas. Se agregaron 6 puntos propios del
  Principio 9.
- El bloque de gobierno de **inteligencia artificial** pasó al Principio 18
  (información y tecnología), sin 2 preguntas duplicadas.
- 15 puntos de interés nuevos: supervisión de ciberseguridad e IA, partes
  relacionadas, ASG/clima, apetito de crédito cuantitativo, terceros, fraude
  digital, estrés de cartera, **mesa de control**, **contraloría de crédito**,
  pruebas de continuidad, calidad de auditoría interna (Normas Globales IIA
  2024), observaciones del supervisor, datos personales (LFPDPPP 2025),
  reportes regulatorios y tablero integrado al Consejo.
- Marcos vigentes: COBIT 2019, Modelo de las Tres Líneas (IIA 2020),
  ISO 31000:2018, ISO/IEC 27001:2022, ISO 22301, ISO/IEC 42001.
- Cálculo corregido: en el Excel la suma de atributos (0–8) se dividía entre
  un número fijo de renglones que no siempre coincidía con las preguntas.
- Normativa ampliada para SOCAP, SOFIPO y SOFOM, y glosario con apetito al
  riesgo, KRI, mesa de control, contraloría de crédito, IMOR e ICOR.

Cada punto conserva su identificador del Excel (etiqueta «Excel x.y.z»).
Verifique con el área jurídica la vigencia de la normativa listada.

## Guardado y respaldos

- **Automático en el navegador** (`localStorage`) en cada cambio.
- **Respaldo JSON** (*Administración → Respaldos*) con huella SHA-256 de
  integridad; **respaldo cifrado** opcional (AES-256-GCM con frase).
- **Autoguardado en archivo local** (Chrome/Edge): cada cambio se escribe
  también en un `.json` elegido por el usuario (equipo o carpeta de red).
- **Restauración** desde la pantalla inicial o desde Administración (antes de
  reemplazar se descarga un respaldo de lo actual).
- Recordatorio en la barra superior cuando el último respaldo es antiguo.

## Integraciones

*Integraciones* exporta e importa información con otras herramientas:

- **CSV** (UTF-8, compatible con Excel) por entidad: cédula de evaluación,
  hallazgos, plan de auditoría, planes de solución, matriz de riesgos,
  valores de KRI, revisiones de mesa de control y bitácora. Hay plantillas
  descargables.
- **Paquete JSON `seci.intercambio`** por área (auditoría interna, crédito,
  riesgos o completo), con resumen de madurez. El formato está documentado en
  la pestaña *Formato de intercambio*.
- **Conectores REST**: Sistemas configura URL y token; cada área envía (POST)
  o recibe (GET) paquetes. El servicio debe usar HTTPS y permitir CORS.
- **Sistema de Administración de Riesgos de Crédito** (este repositorio): la
  cartera se carga con el mismo lay out CSV (`docs/layout_carga.md`); se
  guardan solo cifras agregadas y los 20 principales acreditados.

## Seguridad: alcance y límites

- Contraseñas con PBKDF2-SHA256 (150 000 iteraciones) y sal por usuario;
  política mínima de 8 caracteres con letras y números; bloqueo de 10 minutos
  tras 5 intentos fallidos; cierre de sesión por inactividad.
- Permisos por perfil en cada acción y bitácora encadenada con SHA-256
  (*Verificar integridad* detecta modificaciones).
- Es una aplicación local: quien tenga acceso al equipo y al perfil del
  navegador puede leer los datos almacenados. Proteja el equipo con
  contraseña, use los respaldos cifrados y no la publique en un servidor
  abierto. El control de acceso es organizacional, no sustituye una solución
  con servidor central.

## Desarrollo

El HTML se genera a partir de las fuentes:

```
coso_erm/
├── SECI_COSO_ERM_2026.html        # sistema listo para usar (generado)
├── datos/
│   ├── fuente_excel.json          # extraído del Excel original
│   └── banco_coso_erm_2026.json   # banco actualizado 2026 (generado)
├── herramientas/
│   ├── extraer_excel.py           # Excel → fuente_excel.json (requiere openpyxl)
│   └── construir.py               # fuente + actualizaciones + src → HTML
└── src/                           # app.html, estilos.css y módulos JS
```

```bash
# (opcional) volver a extraer del Excel
pip install openpyxl
python coso_erm/herramientas/extraer_excel.py "1._Eval_COSO_ERM_2026.xlsx"

# generar banco y HTML
python coso_erm/herramientas/construir.py
```
