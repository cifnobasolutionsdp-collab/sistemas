"""Genera un archivo CSV de ejemplo conforme al lay out de carga
(``data/layout_ejemplo.csv``), usando las claves de los catálogos sembrados.

Uso:  python scripts/generar_layout_ejemplo.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

rng = random.Random(7)

FILAS = [
    # periodo, folio, socio, producto, sucursal, moneda, actividad, localidad,
    # garantia, monto, vigente, vencido, mora, plazo, tasa, otorgado, vence
    ["2026-07", "NV00001", "Laura Mendoza Ríos", "PPER", "MTY01", "MXN", "ACT01", "LOC01", "GAVA", 45000, 38200.50, 0, 0, 24, 27.5, "2025-10-15", "2027-10-15"],
    ["2026-07", "NV00002", "Carlos Estrada Peña", "PCOM", "CDMX01", "MXN", "ACT02", "LOC03", "GPRE", 350000, 280000, 21000, 35, 36, 18.9, "2025-03-01", "2028-03-01"],
    ["2026-07", "NV00003", "Sofía Nava Cortés", "PVIV", "QRO02", "MXN", "ACT01", "LOC04", "GHIP", 950000, 910500.25, 0, 0, 60, 11.2, "2026-01-20", "2031-01-20"],
    ["2026-07", "NV00004", "Andrés Beltrán Solís", "PAGR", "OAX01", "MXN", "ACT03", "LOC05", "GSIN", 120000, 60000, 48000, 75, 18, 15.0, "2025-06-10", "2026-12-10"],
    ["2026-07", "NV00005", "Norma Ibarra Luna", "PNOM", "SALT02", "MXN", "ACT01", "LOC02", "GLIQ", 30000, 24500, 0, 0, 12, 23.8, "2026-02-05", "2027-02-05"],
]

ENCABEZADOS = [
    "periodo", "folio", "socio", "producto", "sucursal", "moneda", "actividad",
    "localidad", "garantia", "monto_original", "saldo_vigente", "saldo_vencido",
    "dias_mora", "plazo_meses", "tasa_anual", "fecha_otorgamiento", "fecha_vencimiento",
]


def main() -> None:
    destino = Path(__file__).resolve().parent.parent / "data" / "layout_ejemplo.csv"
    destino.parent.mkdir(exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(ENCABEZADOS)
        escritor.writerows(FILAS)
    print(f"Archivo de ejemplo generado en {destino}")


if __name__ == "__main__":
    main()
