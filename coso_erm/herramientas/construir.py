"""Construye el banco de preguntas actualizado 2026 y el HTML autocontenido.

Uso:
    python coso_erm/herramientas/construir.py

Entradas:
  * ``coso_erm/datos/fuente_excel.json``  (generado por ``extraer_excel.py``)
  * ``coso_erm/src/app.html``             (plantilla de la aplicación)
  * ``coso_erm/src/estilos.css`` y ``coso_erm/src/*.js`` (estilos y módulos)

Salidas:
  * ``coso_erm/datos/banco_coso_erm_2026.json``  (banco actualizado, legible)
  * ``coso_erm/SECI_COSO_ERM_2026.html``          (sistema completo en un archivo)

Todas las actualizaciones al contenido del Excel original se declaran aquí y
quedan listadas en ``cambios`` dentro del banco, para que el Comité de
Auditoría pueda revisarlas.
"""
import copy
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "datos" / "fuente_excel.json"
BANCO = RAIZ / "datos" / "banco_coso_erm_2026.json"
PLANTILLA = RAIZ / "src" / "app.html"
ESTILOS = RAIZ / "src" / "estilos.css"
# Orden de concatenación de los módulos JavaScript.
MODULOS_JS = ["app.js", "ui.js", "vistas_eval.js", "vistas_lineas.js", "vistas_sis.js"]
SALIDA = RAIZ / "SECI_COSO_ERM_2026.html"
VERSION_BANCO = "2026.1"

# Ponderaciones por componente tomadas de la hoja "Resultados".
PESOS = {"GC": 0.25, "EST": 0.20, "REV": 0.15, "ICR": 0.25, "DES": 0.15}

# Atributos a-h de la hoja "Criterios": cada nivel exige todos los atributos
# hasta cierto índice.
ATRIBUTOS = [
    {"k": "a", "n": "Existe", "ciclo": "Definir", "ev": "Nombre del documento (política, procedimiento, actividad)."},
    {"k": "b", "n": "Diseñada", "ciclo": "Definir", "ev": "La evidencia corresponde a lo solicitado y está alineada con lineamientos de la Empresa, sector, reguladores o prácticas internacionales."},
    {"k": "c", "n": "Aprobado", "ciclo": "Aprobar", "ev": "Resolución, acta u otro acto administrativo de aprobación por la autoridad facultada (número, quién, cargo, fecha)."},
    {"k": "d", "n": "Difundido", "ciclo": "Difundir", "ev": "Cursos, reuniones, boletines, correo, intranet u otros medios de difusión en el periodo evaluado."},
    {"k": "e", "n": "Implementado", "ciclo": "Documentar y medir", "ev": "Políticas, procedimientos y actividades que evidencian la implementación conforme a la documentación vigente."},
    {"k": "f", "n": "Responsable", "ciclo": "Documentar y medir", "ev": "Acto administrativo o función (MOF) que designa al responsable."},
    {"k": "g", "n": "Funcionamiento", "ciclo": "Documentar y medir", "ev": "Registros que evidencian la operación con la frecuencia y cuidado debidos (al menos tres meses)."},
    {"k": "h", "n": "Mejora continua", "ciclo": "Revisar y mejorar", "ev": "Actualización o mejora documentada dentro de los últimos dos años (resolución, fecha de última actualización, automatización)."},
]
NIVELES = [
    {"nivel": 0, "requiere": 0, "t": "No existen actividades diseñadas para cubrir el requerimiento."},
    {"nivel": 1, "requiere": 2, "t": "Existen actividades diseñadas pero no están documentadas en políticas y/o procedimientos ni aprobadas."},
    {"nivel": 2, "requiere": 4, "t": "Las actividades están diseñadas, documentadas, aprobadas y difundidas; en proceso de implementación."},
    {"nivel": 3, "requiere": 5, "t": "Además, el control se implementó recientemente conforme a la documentación vigente."},
    {"nivel": 4, "requiere": 7, "t": "Además, existe responsable asignado y registros que evidencian su funcionamiento (al menos tres meses)."},
    {"nivel": 5, "requiere": 8, "t": "Además, el control fue mejorado o la documentación se actualizó en los últimos dos años (mejora continua)."},
]

TEXTOS_ACTUALIZADOS = {
    "1.1.1": "¿Los miembros del Consejo de Administración y otros órganos directivos comprenden y aplican los marcos de referencia para la evaluación de riesgos y control interno (COSO ERM 2017, COSO Control Interno 2013, Modelo de las Tres Líneas del IIA 2020, ISO 31000:2018 y COBIT 2019) en sus procesos de toma de decisiones?",
    "5.19.5": "¿Se elabora formalmente un informe periódico para el Consejo de Administración y Vigilancia, la Gerencia General u órgano equivalente, sobre el estado de los sistemas informáticos y la seguridad de la información (COBIT 2019 / ISO/IEC 27001:2022)?",
}

# Preguntas que se eliminan por duplicar a otra del mismo bloque.
DUPLICADAS = {
    "2.8.20": "2.8.9",   # revisión de proveedores de IA
    "2.8.25": "2.8.7",   # sesgos en IA
}

NUEVO_P9 = [
    "¿Los objetivos de negocio (colocación, captación, rentabilidad, morosidad, liquidez y solvencia) se derivan formalmente del plan estratégico y son aprobados por el Consejo de Administración?",
    "¿Cada objetivo de negocio tiene métricas, metas y tolerancias definidas (variación aceptable del desempeño) congruentes con el apetito al riesgo?",
    "¿Los objetivos se despliegan en cascada a sucursales, áreas y puestos clave, con responsables y fechas de cumplimiento?",
    "¿Se verifica que los objetivos de crecimiento de cartera no excedan los límites de concentración, capacidad de originación y control de la mesa de control?",
    "¿Los objetivos consideran requerimientos regulatorios (capitalización, liquidez, reservas preventivas) y su cumplimiento se monitorea al menos mensualmente?",
    "¿Se revisan y, en su caso, ajustan los objetivos de negocio cuando cambian el contexto o el perfil de riesgo de la Institución?",
]

# Nuevos puntos de interés 2026: (principio, texto, tema).
NUEVAS = [
    (1, "¿El Consejo de Administración supervisa expresamente los riesgos de ciberseguridad, tecnológicos y de uso de inteligencia artificial, recibiendo reportes al menos semestrales sobre incidentes, vulnerabilidades y planes de remediación?", "Ciberseguridad"),
    (4, "¿Se identifican, aprueban y revelan los conflictos de interés y las operaciones con personas relacionadas (consejeros, funcionarios y sus familiares), incluidos los créditos relacionados, dentro de los límites regulatorios?", "Crédito"),
    (6, "¿El análisis de contexto incorpora riesgos ambientales, sociales y de gobierno corporativo (ASG), incluidos fenómenos climáticos que afecten a socios, garantías o regiones atendidas?", "ASG"),
    (7, "¿El apetito al riesgo se expresa en límites cuantitativos medibles para el riesgo de crédito (IMOR, ICOR, concentración por acreditado y sector, cobertura de reservas) con alertas tempranas y responsables de escalamiento?", "Crédito"),
    (10, "¿Se identifican y evalúan los riesgos derivados de terceros y proveedores críticos (core bancario, nube, corresponsales, cobranza externa) con debida diligencia y cláusulas de auditoría?", "Terceros"),
    (10, "¿Se identifican y valoran los riesgos de fraude interno y externo, incluido el fraude digital (suplantación de identidad, ingeniería social, robo de cuentas)?", "Fraude"),
    (11, "¿Se realizan pruebas de estrés y análisis de escenarios sobre la cartera de crédito (pérdida esperada, pérdida no esperada / VaR de crédito, concentración) y sus resultados se presentan al Comité de Riesgos?", "Crédito"),
    (13, "¿La mesa de control verifica, antes de la disposición del crédito, la integración completa del expediente, las autorizaciones por nivel facultado, las garantías y la consulta a sociedades de información crediticia, registrando las excepciones?", "Mesa de control"),
    (13, "¿La contraloría de crédito revisa de forma independiente y periódica la originación, seguimiento y recuperación de la cartera, el cumplimiento de políticas y la atención de excepciones?", "Contraloría de crédito"),
    (16, "¿Los planes de continuidad del negocio y de recuperación ante desastres se prueban al menos una vez al año y los resultados se documentan con acciones de mejora?", "Continuidad"),
    (17, "¿La función de auditoría interna cuenta con un programa de aseguramiento y mejora de la calidad, incluyendo una evaluación externa al menos cada cinco años, conforme a las Normas Globales de Auditoría Interna (IIA, 2024)?", "Auditoría interna"),
    (17, "¿Se da seguimiento formal a las observaciones de la autoridad supervisora (CNBV y, en su caso, Comité de Supervisión Auxiliar) hasta su solventación?", "Regulatorio"),
    (18, "¿El tratamiento de datos personales de socios y clientes cumple con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares vigente (2025), incluyendo avisos de privacidad, derechos ARCO y medidas de seguridad?", "Datos personales"),
    (19, "¿Los reportes regulatorios se envían en tiempo y forma a la autoridad, con controles de calidad de datos, conciliación contable y evidencia de revisión previa?", "Regulatorio"),
    (20, "¿Se presenta al Consejo un tablero integrado con los resultados de auditoría interna, contraloría interna, contraloría de crédito / mesa de control y administración de riesgos, con el estatus de los planes de acción?", "Integración"),
]

NORMATIVA_EXTERNA = [
    ("Ley para Regular las Actividades de las Sociedades Cooperativas de Ahorro y Préstamo (LRASCAP)", "SOCAP"),
    ("Disposiciones de carácter general aplicables a las SOCAP (CNBV)", "SOCAP"),
    ("Ley de Ahorro y Crédito Popular y sus disposiciones (SOFIPO)", "SOFIPO"),
    ("Ley General de Organizaciones y Actividades Auxiliares del Crédito (SOFOM)", "SOFOM"),
    ("Ley General de Sociedades Mercantiles (LGSM)", "General"),
    ("Ley General de Sociedades Cooperativas (LGSC)", "General"),
    ("Ley del Impuesto sobre la Renta", "Fiscal"),
    ("Ley del Impuesto al Valor Agregado", "Fiscal"),
    ("Ley Federal del Trabajo", "Laboral"),
    ("Ley de Protección y Defensa al Usuario de Servicios Financieros y disposiciones CONDUSEF", "Usuarios"),
    ("Ley para la Transparencia y Ordenamiento de los Servicios Financieros y circulares de Banco de México (CAT, GAT, contratos, estados de cuenta)", "Usuarios"),
    ("Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita y disposiciones PLD/FT aplicables", "PLD/FT"),
    ("Ley para Regular las Sociedades de Información Crediticia", "Crédito"),
    ("Ley Federal de Protección de Datos Personales en Posesión de los Particulares (2025)", "Datos personales"),
    ("COSO ERM — Gestión del riesgo empresarial: integración con estrategia y desempeño (2017)", "Marco"),
    ("COSO Control Interno — Marco Integrado (2013)", "Marco"),
    ("IIA — Normas Globales de Auditoría Interna (2024)", "Marco"),
    ("IIA — Modelo de las Tres Líneas (2020)", "Marco"),
    ("ISO 31000:2018 Gestión del riesgo", "Marco"),
    ("ISO/IEC 27001:2022 Seguridad de la información", "Marco"),
    ("ISO 22301:2019 Continuidad del negocio", "Marco"),
    ("ISO/IEC 42001:2023 Sistemas de gestión de inteligencia artificial", "Marco"),
    ("COBIT 2019 Gobierno y gestión de TI", "Marco"),
]

GLOSARIO_NUEVO = [
    ("Apetito al riesgo", "Cantidad y tipo de riesgo que la Institución está dispuesta a aceptar en la búsqueda de su misión y objetivos; se expresa con límites cuantitativos aprobados por el Consejo."),
    ("Capacidad de riesgo", "Nivel máximo de riesgo que la Institución puede asumir sin comprometer su solvencia, liquidez o continuidad."),
    ("Indicador clave de riesgo (KRI)", "Métrica que anticipa cambios en el perfil de riesgo y se compara con umbrales de apetito y tolerancia para generar alertas tempranas."),
    ("Modelo de las Tres Líneas", "Modelo del IIA (2020) que distingue los roles del órgano de gobierno, la dirección (primera y segunda línea) y la auditoría interna (tercera línea, independiente)."),
    ("Mesa de control", "Función que verifica, antes de la disposición del crédito, que el expediente esté completo, las autorizaciones correspondan al nivel facultado y se cumplan las condiciones aprobadas."),
    ("Contraloría de crédito", "Función que supervisa de forma independiente el proceso de crédito (originación, seguimiento y recuperación) y el cumplimiento de las políticas aprobadas."),
    ("Hallazgo de auditoría", "Resultado de comparar la condición observada con el criterio aplicable; se documenta con condición, criterio, causa, efecto y recomendación."),
    ("Plan de solución (PS)", "Conjunto de acciones, responsables, fechas, presupuesto y entregables para corregir una deficiencia de control interno."),
    ("IMOR", "Índice de morosidad: cartera vencida entre cartera total."),
    ("ICOR", "Índice de cobertura: reservas preventivas entre cartera vencida."),
    ("Bitácora de auditoría", "Registro cronológico e inalterable de las acciones realizadas por los usuarios del sistema, encadenado con huellas digitales (hash) para detectar alteraciones."),
]


def construir_banco():
    fuente = json.loads(FUENTE.read_text(encoding="utf-8"))
    demo_fuente = fuente["demo"]
    cambios, demo = [], {}
    componentes = []
    for comp in fuente["components"]:
        c = {"code": comp["code"], "name": comp["name"], "peso": PESOS[comp["code"]], "principles": []}
        for p in comp["principles"]:
            c["principles"].append({"n": p["n"], "t": p["t"], "q": copy.deepcopy(p["q"])})
        componentes.append(c)
    principios = {p["n"]: p for c in componentes for p in c["principles"]}

    # 1) Reestructura de Estrategia: el bloque de estrategias alternativas estaba
    #    bajo el Principio 9 y el bloque de IA bajo el Principio 8.
    alternativas = principios[9]["q"]
    ia = principios[8]["q"]
    principios[8]["q"] = alternativas
    principios[9]["q"] = [{"id": "", "t": t, "tema": "Objetivos", "nuevo": True} for t in NUEVO_P9]
    cambios.append("Principio 8 (Evalúa estrategias alternativas): recibe los puntos de interés de estrategias alternativas que en el Excel estaban bajo el Principio 9.")
    cambios.append("Principio 9 (Formula objetivos de negocio): se redactan 6 puntos de interés propios del principio (antes no tenía preguntas sobre objetivos).")

    # 2) Bloque de IA -> Principio 18 (información y tecnología), sin duplicados.
    ia_limpio = [dict(q, tema="Inteligencia artificial") for q in ia if q["id"] not in DUPLICADAS]
    principios[18]["q"].extend(ia_limpio)
    cambios.append(f"Los {len(ia)} puntos de interés de gobierno de inteligencia artificial se trasladan al Principio 18 (Aprovecha la información y la tecnología); se eliminan {len(DUPLICADAS)} duplicados ({', '.join(f'{k}≈{v}' for k, v in DUPLICADAS.items())}).")

    # 3) Preguntas nuevas.
    for n, texto, tema in NUEVAS:
        principios[n]["q"].append({"id": "", "t": texto, "tema": tema, "nuevo": True})
    cambios.append(f"Se agregan {len(NUEVAS)} puntos de interés 2026: ciberseguridad, partes relacionadas, ASG, apetito de crédito, terceros, fraude, estrés de cartera, mesa de control, contraloría de crédito, continuidad, calidad de auditoría interna, observaciones del supervisor, datos personales, reportes regulatorios y tablero integrado.")

    # 4) Renumeración (componente.principio.consecutivo) conservando el ID original.
    for ci, c in enumerate(componentes, start=1):
        for p in c["principles"]:
            for k, q in enumerate(p["q"], start=1):
                orig = q.get("id") or None
                q["id"] = f"{ci}.{p['n']}.{k}"
                if orig:
                    q["orig"] = orig
                    if orig in TEXTOS_ACTUALIZADOS:
                        q["t"] = TEXTOS_ACTUALIZADOS[orig]
                        q["actualizado"] = True
                    if orig in demo_fuente:
                        demo[q["id"]] = demo_fuente[orig]
    cambios.append("Se actualizan referencias a marcos vigentes: COBIT 5 → COBIT 2019, «3 líneas de defensa» → Modelo de las Tres Líneas (IIA 2020), ISO 31000:2018, ISO/IEC 27001:2022.")
    cambios.append("Los puntos de interés se renumeran como componente.principio.consecutivo; cada uno conserva su ID del Excel en «orig» para trazabilidad.")
    cambios.append("Cálculo corregido: el nivel de cada punto de interés (0-5) se obtiene de la tabla de Criterios (atributos a-h acumulativos); la calificación del principio es el promedio de sus puntos contestados. En el Excel la suma de atributos (0-8) se dividía entre un número fijo de renglones que no siempre coincidía con el número de preguntas.")
    cambios.append("Normativa: se amplía con marcos de referencia vigentes y leyes aplicables a SOCAP, SOFIPO y SOFOM; glosario: se agregan términos de apetito al riesgo, KRI, Tres Líneas, mesa de control, contraloría de crédito e indicadores de cartera.")

    glosario = [[t.split(". ", 1)[-1].rstrip(":"), d] for t, d in fuente["glosario"] if d]
    glosario += [list(x) for x in GLOSARIO_NUEVO]
    glosario.sort(key=lambda x: x[0].lower())

    internos = [n.title() for n in fuente["normativa"]
                if n.upper().startswith(("MANUAL", "REGLAMENTO"))]
    normativa = [{"nombre": n, "tipo": "Externa", "ambito": a} for n, a in NORMATIVA_EXTERNA]
    normativa += [{"nombre": n, "tipo": "Interna", "ambito": "Manual"} for n in internos]

    return {
        "version": VERSION_BANCO,
        "components": componentes,
        "atributos": ATRIBUTOS,
        "niveles": NIVELES,
        "madurez": [{"n": m[0], "rango": m[1], "t": m[2]} for m in fuente["madurez"]],
        "glosario": glosario,
        "normativa": normativa,
        "demo": demo,
        "cambios": cambios,
    }


def main():
    banco = construir_banco()
    BANCO.write_text(json.dumps(banco, ensure_ascii=False, indent=1), encoding="utf-8")
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    marca = "/*__BANCO__*/null"
    if marca not in plantilla:
        raise SystemExit(f"La plantilla no contiene la marca {marca}")
    datos = json.dumps(banco, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    js = "\n".join((RAIZ / "src" / m).read_text(encoding="utf-8") for m in MODULOS_JS)
    if "</script" in js.lower():
        raise SystemExit("Los módulos JS no deben contener la secuencia </script")
    html = (plantilla.replace("/*__CSS__*/", ESTILOS.read_text(encoding="utf-8"))
            .replace("/*__JS__*/", js)
            .replace(marca, datos))
    SALIDA.write_text(html, encoding="utf-8")
    n = sum(len(p["q"]) for c in banco["components"] for p in c["principles"])
    print(f"Banco {VERSION_BANCO}: {n} puntos de interés -> {BANCO.name}")
    print(f"Sistema -> {SALIDA} ({SALIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
