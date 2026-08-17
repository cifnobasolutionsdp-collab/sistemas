"""Plantillas de proceso para puestos típicos de SOCAPS, SOFIPOS y SOFOMES.

Cada plantilla precarga la descripción de la oferta y las preguntas de filtro
(«killer questions») habituales del sector financiero popular, incluidas las
verificaciones de cumplimiento (certificaciones, historial y disponibilidad).
También expone :func:`generar_descripcion`, el asistente de redacción que
produce una descripción clara y concisa a partir de los datos de la vacante.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OpcionPlantilla:
    texto: str
    peso: float = 0.0
    excluyente: bool = False


@dataclass
class PreguntaPlantilla:
    texto: str
    tipo: str = "cerrada"  # cerrada | abierta
    opciones: list[OpcionPlantilla] = field(default_factory=list)


def _si_no(peso_si: float, no_excluyente: bool = False, peso_no: float = 0.0):
    return [
        OpcionPlantilla("Sí", peso_si),
        OpcionPlantilla("No", peso_no, excluyente=no_excluyente),
    ]


@dataclass
class PlantillaProceso:
    slug: str
    nombre: str
    posicion: str
    area: str
    jornada: str = "Jornada Completa"
    modalidad: str = "Presencial"
    descripcion: str = ""
    preguntas: list[PreguntaPlantilla] = field(default_factory=list)


PLANTILLAS: dict[str, PlantillaProceso] = {}


def _registrar(p: PlantillaProceso) -> None:
    PLANTILLAS[p.slug] = p


_registrar(
    PlantillaProceso(
        slug="asesor-credito",
        nombre="Asesor de Crédito (SOCAP / SOFIPO / SOFOM)",
        posicion="Asesor de Crédito",
        area="Crédito",
        descripcion=(
            "Buscamos un Asesor de Crédito para promover y colocar productos de "
            "crédito, integrar expedientes conforme a la normativa CNBV, analizar "
            "la capacidad de pago de socios y clientes, y dar seguimiento a la "
            "recuperación de cartera. Se requiere orientación a resultados, trato "
            "cercano con socios y conocimiento del sector de finanzas populares."
        ),
        preguntas=[
            PreguntaPlantilla(
                "¿Cuentas con experiencia mínima de 1 año colocando crédito en "
                "SOCAPS, SOFIPOS, SOFOMES o banca?",
                opciones=_si_no(10, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "¿Conoces el proceso de integración de expedientes de crédito "
                "conforme a las disposiciones de la CNBV?",
                opciones=_si_no(8),
            ),
            PreguntaPlantilla(
                "¿Estás dispuesto a realizar trabajo de campo (visitas a socios y "
                "prospección en comunidades)?",
                opciones=_si_no(7, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "Cuéntanos brevemente tu experiencia en colocación y recuperación "
                "de cartera.",
                tipo="abierta",
            ),
        ],
    )
)
_registrar(
    PlantillaProceso(
        slug="cajero",
        nombre="Cajero / Ejecutivo de Ventanilla",
        posicion="Cajero de Sucursal",
        area="Operaciones",
        descripcion=(
            "Buscamos un Cajero de Sucursal responsable de la atención en "
            "ventanilla: depósitos, retiros, pagos de crédito y captación de "
            "ahorro, con apego a las políticas de control de efectivo y a la "
            "normativa de Prevención de Lavado de Dinero (PLD). Se requiere "
            "precisión, honestidad comprobable y vocación de servicio al socio."
        ),
        preguntas=[
            PreguntaPlantilla(
                "¿Tienes experiencia en manejo de efectivo (caja, ventanilla o "
                "punto de venta)?",
                opciones=_si_no(10, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "¿Cuentas con carta de no antecedentes penales vigente o estás en "
                "posibilidad de tramitarla?",
                opciones=_si_no(8, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "¿Conoces los lineamientos básicos de Prevención de Lavado de "
                "Dinero (PLD)?",
                opciones=_si_no(6),
            ),
            PreguntaPlantilla(
                "¿Tienes disponibilidad para laborar fines de semana con rol de "
                "descanso entre semana?",
                opciones=_si_no(5),
            ),
        ],
    )
)
_registrar(
    PlantillaProceso(
        slug="gerente-sucursal",
        nombre="Gerente de Sucursal",
        posicion="Gerente de Sucursal",
        area="Dirección de Sucursales",
        descripcion=(
            "Buscamos un Gerente de Sucursal para dirigir la operación integral "
            "de la unidad: metas de colocación y captación, calidad de cartera, "
            "control interno, cumplimiento normativo (CNBV, PLD) y desarrollo del "
            "equipo. Se requiere liderazgo, análisis financiero y experiencia en "
            "el sector de ahorro y crédito popular."
        ),
        preguntas=[
            PreguntaPlantilla(
                "¿Cuentas con al menos 3 años de experiencia gerencial en "
                "instituciones financieras?",
                opciones=_si_no(10, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "¿Has administrado indicadores de cartera (colocación, IMOR, "
                "recuperación) y metas de captación?",
                opciones=_si_no(9),
            ),
            PreguntaPlantilla(
                "¿Cuentas con licenciatura concluida en áreas económico-"
                "administrativas?",
                opciones=_si_no(6),
            ),
            PreguntaPlantilla(
                "Describe un logro medible al frente de una sucursal o equipo "
                "comercial.",
                tipo="abierta",
            ),
        ],
    )
)
_registrar(
    PlantillaProceso(
        slug="analista-riesgos",
        nombre="Analista de Crédito y Riesgos",
        posicion="Analista de Crédito y Riesgos",
        area="Riesgos",
        modalidad="Híbrido",
        descripcion=(
            "Buscamos un Analista de Crédito y Riesgos para evaluar solicitudes, "
            "calificar cartera conforme a la metodología CNBV, dar seguimiento a "
            "límites y reportes regulatorios, y apoyar el provisionamiento de "
            "reservas preventivas. Se requiere manejo de Excel avanzado y gusto "
            "por el análisis cuantitativo."
        ),
        preguntas=[
            PreguntaPlantilla(
                "¿Has trabajado con calificación de cartera o reportes "
                "regulatorios (CNBV, R04, buró de crédito)?",
                opciones=_si_no(10),
            ),
            PreguntaPlantilla(
                "¿Dominas Excel avanzado (tablas dinámicas, funciones de "
                "búsqueda, macros básicas)?",
                opciones=_si_no(8, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "¿Cuentas con formación en actuaría, economía, finanzas o afín?",
                opciones=_si_no(6),
            ),
        ],
    )
)
_registrar(
    PlantillaProceso(
        slug="promotor-captacion",
        nombre="Promotor de Captación y Ahorro",
        posicion="Promotor de Captación",
        area="Comercial",
        descripcion=(
            "Buscamos un Promotor de Captación para afiliar nuevos socios, "
            "promover productos de ahorro e inversión y participar en campañas de "
            "educación financiera en comunidades. Se requiere facilidad de "
            "palabra, disponibilidad para trabajo de campo y compromiso con la "
            "inclusión financiera."
        ),
        preguntas=[
            PreguntaPlantilla(
                "¿Tienes experiencia en ventas o promoción de servicios "
                "financieros?",
                opciones=_si_no(9),
            ),
            PreguntaPlantilla(
                "¿Cuentas con disponibilidad para trasladarte dentro de la plaza "
                "y comunidades cercanas?",
                opciones=_si_no(7, no_excluyente=True),
            ),
            PreguntaPlantilla(
                "¿Te sientes cómodo hablando en público y organizando pláticas de "
                "educación financiera?",
                opciones=_si_no(5),
            ),
        ],
    )
)


def generar_descripcion(
    posicion: str,
    area: str = "",
    jornada: str = "",
    modalidad: str = "",
    sucursal: str = "",
) -> str:
    """Asistente de redacción: genera una descripción clara y concisa."""
    partes = [
        f"Estamos en búsqueda de un {posicion.strip() or 'colaborador'} para unirse a "
        "nuestro equipo"
    ]
    if sucursal:
        partes.append(f"en la sucursal {sucursal}")
    if area:
        partes.append(f"dentro del área de {area}")
    encabezado = " ".join(partes) + "."
    condiciones = []
    if jornada:
        condiciones.append(f"jornada {jornada.lower()}")
    if modalidad:
        condiciones.append(f"modalidad {modalidad.lower()}")
    cuerpo = (
        " La persona seleccionada participará en la atención y desarrollo de socios y "
        "clientes, con apego a las políticas internas y a la normativa aplicable al "
        "sector financiero (CNBV y Prevención de Lavado de Dinero). Se requiere "
        "atención al detalle, habilidades de comunicación, honestidad comprobable y "
        "vocación de servicio."
    )
    cierre = f" Ofrecemos {', '.join(condiciones)}, capacitación continua y desarrollo profesional." if condiciones else ""
    return encabezado + cuerpo + cierre
