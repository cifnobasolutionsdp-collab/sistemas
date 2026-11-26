"""Genera archivos de ejemplo del módulo de Monitoreo Financiero y los importa.

Crea en ``data/``:
  * ``balanza_socap_AAAA-MM-DD.csv``  balanzas de comprobación (cuentas de
    mayor y de detalle) de una SOCAP de demostración en tres cortes.
  * ``complementarios_socap_AAAA-MM-DD.csv``  datos complementarios
    (morosidad por antigüedad, castigos, reservas por etapa, socios...).
  * ``estados_sofom_AAAA-MM-DD.csv``  lay out de estados financieros de una
    SOFOM de demostración.

Uso:  python scripts/seed_monitoreo.py [--solo-archivos]
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
DATA = RAIZ / "data"

M = 1_000_000

# Cuentas de detalle: (cuenta, descripción, importe base al 30/09/2026 en pesos)
BALANCE_SOCAP = [
    ("110101", "Caja general", 2.5 * M),
    ("110201", "Bancos cuenta de cheques", 11.0 * M),
    ("110202", "Bancos inversión a la vista", 7.0 * M),
    ("120101", "Pagarés con rendimiento liquidable al vencimiento", 22.0 * M),
    ("120201", "Certificados bursátiles largo plazo", 1.5 * M),
    ("130101", "Cartera etapa 1 — consumo", 98.0 * M),
    ("130102", "Cartera etapa 1 — comercial", 37.0 * M),
    ("130103", "Cartera etapa 1 — vivienda", 15.0 * M),
    ("130201", "Cartera etapa 2 — consumo", 9.0 * M),
    ("130301", "Cartera etapa 3 — consumo", 10.5 * M),
    ("130302", "Cartera etapa 3 — comercial", 3.5 * M),
    ("130401", "Estimación preventiva para riesgos crediticios", 11.5 * M),
    ("140101", "Deudores diversos", 2.0 * M),
    ("150101", "Bienes adjudicados", 1.2 * M),
    ("160101", "Inmuebles", 6.5 * M),
    ("160201", "Mobiliario y equipo", 2.5 * M),
    ("170101", "Inversiones permanentes en entidades de segundo piso", 0.3 * M),
    ("180101", "Pagos anticipados y cargos diferidos", 1.5 * M),
    ("210101", "Depósitos a la vista", 70.0 * M),
    ("210201", "Depósitos a plazo", 0.0),  # partida de cuadre
    ("220101", "Préstamos de banca de desarrollo", 6.0 * M),
    ("230101", "Acreedores diversos", 3.0 * M),
    ("240101", "Créditos diferidos", 1.0 * M),
    ("310101", "Certificados de aportación ordinarios", 9.0 * M),
    ("320101", "Fondo de reserva", 14.0 * M),
    ("320201", "Resultado de ejercicios anteriores", 4.0 * M),
]
# Resultados acumulados a 9 meses (se escalan por meses transcurridos)
RESULTADOS_SOCAP = [
    ("410101", "Intereses de cartera de crédito", 24.0 * M),
    ("410201", "Intereses de disponibilidades e inversiones", 2.6 * M),
    ("410301", "Intereses de inversiones de largo plazo", 0.08 * M),
    ("420101", "Comisiones cobradas", 1.2 * M),
    ("430101", "Otros ingresos", 0.5 * M),
    ("510101", "Intereses por depósitos", 7.5 * M),
    ("510201", "Intereses por préstamos bancarios", 0.45 * M),
    ("520101", "Comisiones pagadas", 0.3 * M),
    ("530101", "Estimación preventiva para riesgos crediticios", 3.2 * M),
    ("540101", "Remuneraciones y prestaciones", 7.4 * M),
    ("540201", "Gastos de administración y promoción", 4.7 * M),
    ("550101", "Otros gastos", 0.33 * M),
    ("560101", "Impuestos y PTU", 0.5 * M),
]
MAYORES = {
    "1": "ACTIVO", "11": "Disponibilidades", "1101": "Caja", "1102": "Bancos", "12": "Inversiones en valores",
    "1201": "Inversiones de corto plazo", "1202": "Inversiones de largo plazo", "13": "Cartera de crédito",
    "1301": "Cartera etapa 1", "1302": "Cartera etapa 2", "1303": "Cartera etapa 3", "1304": "Estimación preventiva",
    "14": "Otras cuentas por cobrar", "1401": "Deudores diversos", "15": "Bienes adjudicados", "1501": "Bienes adjudicados",
    "16": "Propiedades, mobiliario y equipo", "1601": "Inmuebles", "1602": "Mobiliario y equipo", "17": "Inversiones permanentes",
    "1701": "Inversiones permanentes", "18": "Otros activos", "1801": "Cargos diferidos", "2": "PASIVO", "21": "Captación tradicional",
    "2101": "Depósitos de exigibilidad inmediata", "2102": "Depósitos a plazo", "22": "Préstamos bancarios", "2201": "Préstamos bancarios",
    "23": "Otras cuentas por pagar", "2301": "Acreedores diversos", "24": "Créditos diferidos", "2401": "Créditos diferidos",
    "3": "CAPITAL", "31": "Capital social", "3101": "Capital social", "32": "Capital ganado", "3201": "Reservas",
    "3202": "Resultado de ejercicios anteriores", "4": "INGRESOS", "41": "Ingresos por intereses", "4101": "Intereses de cartera",
    "4102": "Intereses de disponibilidades", "4103": "Intereses de inversiones LP", "42": "Comisiones cobradas", "4201": "Comisiones cobradas",
    "43": "Otros ingresos", "4301": "Otros ingresos", "5": "GASTOS", "51": "Gastos por intereses", "5101": "Intereses por depósitos",
    "5102": "Intereses por préstamos", "52": "Comisiones pagadas", "5201": "Comisiones pagadas", "53": "Estimación preventiva",
    "5301": "Estimación preventiva", "54": "Gastos de administración", "5401": "Remuneraciones", "5402": "Administración y promoción",
    "55": "Otros gastos", "5501": "Otros gastos", "56": "Impuestos", "5601": "Impuestos y PTU",
}

CORTES_SOCAP = {
    # fecha: (escala de balance, escala por cartera deteriorada, inflación, CETES, tasa empresarial, socios)
    date(2025, 12, 31): (0.90, 0.80, 0.042, 0.090, 0.21, 11850),
    date(2026, 6, 30): (0.96, 0.92, 0.040, 0.080, 0.21, 12320),
    date(2026, 9, 30): (1.00, 1.00, 0.039, 0.075, 0.21, 12610),
}


def _balanza_socap(fecha: date, escala: float, escala_mora: float) -> list[tuple[str, str, float]]:
    detalle = {}
    for cuenta, desc, imp in BALANCE_SOCAP:
        factor = escala_mora if cuenta.startswith(("1302", "1303", "1304")) else escala
        detalle[cuenta] = (desc, round(imp * factor, 2))
    meses = fecha.month
    for cuenta, desc, imp in RESULTADOS_SOCAP:
        detalle[cuenta] = (desc, round(imp * escala * meses / 9, 2))
    # Cuadre con depósitos a plazo
    activo = sum(v for c, (_, v) in detalle.items() if c[0] == "1" and not c.startswith("1304")) - detalle["130401"][1]
    resultado = sum(v for c, (_, v) in detalle.items() if c[0] == "4") - sum(v for c, (_, v) in detalle.items() if c[0] == "5")
    pasivo_capital = sum(v for c, (_, v) in detalle.items() if c[0] in "23") + resultado
    detalle["210201"] = ("Depósitos a plazo", round(activo - pasivo_capital, 2))

    filas = []
    for mayor, desc in MAYORES.items():
        hijos = [c for c in detalle if c.startswith(mayor)]
        if not hijos:
            continue
        signo = lambda c: -1 if c.startswith("1304") else 1  # noqa: E731
        total = sum(detalle[c][1] * signo(c) for c in hijos)
        filas.append((mayor, desc.upper() if len(mayor) == 1 else desc, round(abs(total), 2)))
    filas += [(c, d, v) for c, (d, v) in detalle.items()]
    return sorted(filas, key=lambda f: f[0])


def _complementarios_socap(fecha: date, escala: float, escala_mora: float, params) -> list[tuple[str, float]]:
    infl, cetes, emp, socios = params
    e2, e3 = 9.0 * M * escala_mora, 14.0 * M * escala_mora
    return [
        ("mora_1_12", round(e3 * 0.78, 2)),
        ("mora_mas_12", round(e3 * 0.22, 2)),
        ("castigos_ejercicio", round(0.9 * M * fecha.month / 12, 2)),
        ("castigos_acumulados", round(6.5 * M, 2)),
        ("recuperaciones_acumuladas", round(3.1 * M, 2)),
        ("reserva_etapa1", round(1.9 * M * escala, 2)),
        ("reserva_etapa2", round(1.4 * M * escala_mora, 2)),
        ("reserva_etapa3", round(11.5 * M * escala_mora - 1.9 * M * escala - 1.4 * M * escala_mora, 2)),
        ("cxp_30_dias", round(1.8 * M * escala, 2)),
        ("reserva_liquidez", round(15.5 * M * escala, 2)),
        ("asociados", socios),
        ("inflacion", infl * 100),
        ("tasa_mercado", cetes * 100),
        ("tasa_empresarial", emp * 100),
    ]


SOFOM = {
    date(2025, 12, 31): {
        "bancos": 8.2 * M, "inversiones_cp": 3.0 * M, "cartera_etapa1": 182.0 * M, "cartera_etapa2": 7.5 * M, "cartera_etapa3": 6.8 * M,
        "estimaciones": 8.9 * M, "cuentas_por_cobrar": 1.6 * M, "activo_fijo": 2.1 * M, "otros_activos": 1.2 * M,
        "prestamos_bancarios": 148.0 * M, "cuentas_por_pagar": 2.9 * M, "otros_pasivos": 0.8 * M,
        "capital_social": 30.0 * M, "reservas_capital": 2.4 * M, "resultados_anteriores": 5.6 * M,
        "ing_intereses_cartera": 46.5 * M, "ing_disponibilidades": 0.9 * M, "comisiones_cobradas": 2.4 * M, "otros_ingresos": 0.3 * M,
        "int_prestamos_bancarios": 17.8 * M, "comisiones_pagadas": 0.7 * M, "provisiones": 5.1 * M, "gastos_administracion": 18.6 * M,
        "otros_gastos": 0.4 * M, "impuestos": 1.9 * M,
        "mora_1_12": 5.9 * M, "mora_mas_12": 0.9 * M, "castigos_ejercicio": 2.2 * M, "castigos_acumulados": 7.4 * M,
        "recuperaciones_acumuladas": 2.3 * M, "asociados": 5420, "inflacion": 4.2, "tasa_mercado": 9.0, "tasa_empresarial": 24.0,
    },
    date(2026, 9, 30): {
        "bancos": 6.4 * M, "inversiones_cp": 2.0 * M, "cartera_etapa1": 196.0 * M, "cartera_etapa2": 12.4 * M, "cartera_etapa3": 11.1 * M,
        "estimaciones": 10.2 * M, "cuentas_por_cobrar": 1.9 * M, "activo_fijo": 2.0 * M, "otros_activos": 1.4 * M,
        "prestamos_bancarios": 175.0 * M, "cuentas_por_pagar": 3.1 * M, "otros_pasivos": 0.9 * M,
        "capital_social": 30.0 * M, "reservas_capital": 2.9 * M, "resultados_anteriores": 6.4 * M,
        "ing_intereses_cartera": 37.4 * M, "ing_disponibilidades": 0.5 * M, "comisiones_cobradas": 1.9 * M, "otros_ingresos": 0.2 * M,
        "int_prestamos_bancarios": 15.2 * M, "comisiones_pagadas": 0.6 * M, "provisiones": 5.6 * M, "gastos_administracion": 15.9 * M,
        "otros_gastos": 0.3 * M, "impuestos": 0.6 * M,
        "mora_1_12": 9.3 * M, "mora_mas_12": 1.8 * M, "castigos_ejercicio": 2.4 * M, "castigos_acumulados": 9.8 * M,
        "recuperaciones_acumuladas": 2.6 * M, "asociados": 5710, "inflacion": 3.9, "tasa_mercado": 7.5, "tasa_empresarial": 24.0,
    },
}


def _resultado_sofom(d: dict) -> float:
    from app.monitoreo.rubros import agregados

    return agregados(d)["excedente_neto"]


def _descuadre(d: dict) -> float:
    from app.monitoreo.rubros import agregados

    return agregados(d)["descuadre"]


def generar_archivos() -> list[tuple[str, str, date, Path]]:
    """Escribe los archivos de ejemplo; devuelve (entidad, tipo, fecha, ruta)."""
    DATA.mkdir(exist_ok=True)
    archivos = []
    for fecha, (esc, esc_mora, infl, cetes, emp, socios) in CORTES_SOCAP.items():
        ruta = DATA / f"balanza_socap_{fecha.isoformat()}.csv"
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["cuenta", "descripcion", "saldo_final"])
            for cuenta, desc, saldo in _balanza_socap(fecha, esc, esc_mora):
                w.writerow([cuenta, desc, f"{saldo:.2f}"])
        archivos.append(("CPDEMO", "balanza", fecha, ruta))
        ruta = DATA / f"complementarios_socap_{fecha.isoformat()}.csv"
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["clave", "importe"])
            for clave, imp in _complementarios_socap(fecha, esc, esc_mora, (infl, cetes, emp, socios)):
                w.writerow([clave, f"{imp:.2f}" if isinstance(imp, float) else imp])
        archivos.append(("CPDEMO", "estados", fecha, ruta))
    for fecha, datos in SOFOM.items():
        datos = dict(datos)
        datos["resultado_ejercicio"] = round(_resultado_sofom(datos), 2)
        datos["prestamos_bancarios"] = round(datos["prestamos_bancarios"] + _descuadre(datos), 2)  # cuadre
        ruta = DATA / f"estados_sofom_{fecha.isoformat()}.csv"
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["clave", "importe"])
            for clave, imp in datos.items():
                w.writerow([clave, f"{imp:.2f}" if isinstance(imp, float) else imp])
        archivos.append(("SFDEMO", "estados", fecha, ruta))
    return archivos


def main() -> None:
    archivos = generar_archivos()
    print(f"{len(archivos)} archivos de ejemplo generados en {DATA}.")
    if "--solo-archivos" in sys.argv:
        return
    from app.database import Base, SessionLocal, engine
    from app.monitoreo.importacion import importar_balanza, importar_estados
    from app.monitoreo.modelos import Entidad

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Entidad).filter(Entidad.clave.in_(["CPDEMO", "SFDEMO"])).count():
            print("Las entidades de demostración ya existen; no se vuelven a importar.")
            return
        entidades = {
            "CPDEMO": Entidad(clave="CPDEMO", nombre="Caja Popular Demostración, S.C. de A.P. de R.L. de C.V.", tipo="SOCAP", nivel="Nivel II"),
            "SFDEMO": Entidad(clave="SFDEMO", nombre="Financiera Demostración, S.A. de C.V., SOFOM, E.N.R.", tipo="SOFOM", nivel="E.N.R."),
        }
        db.add_all(entidades.values())
        db.commit()
        for clave, tipo, fecha, ruta in archivos:
            fn = importar_balanza if tipo == "balanza" else importar_estados
            res = fn(db, entidades[clave], fecha, ruta.read_bytes(), ruta.name)
            print(f"  {ruta.name}: {res.estatus}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
