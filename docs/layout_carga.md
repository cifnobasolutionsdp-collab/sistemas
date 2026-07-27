# Lay out de carga de información de cartera

El proceso de **Carga de información** recibe un archivo **CSV** codificado en
UTF-8, con encabezados en la primera fila. Cada renglón representa un crédito
en un periodo determinado. Un ejemplo funcional se encuentra en
`data/layout_ejemplo.csv`.

## Definición de columnas

| # | Columna | Tipo | Obligatoria | Descripción |
|---|---------|------|-------------|-------------|
| 1 | `periodo` | Texto `AAAA-MM` | Sí | Periodo al que corresponde el corte de la cartera (ej. `2026-07`). |
| 2 | `folio` | Texto (máx. 30) | Sí | Identificador único del crédito dentro del periodo. |
| 3 | `socio` | Texto (máx. 150) | Sí | Nombre del socio o acreditado. |
| 4 | `producto` | Clave de catálogo | Sí | Clave del catálogo **Productos de Crédito** (ej. `PPER`). |
| 5 | `sucursal` | Clave de catálogo | Sí | Clave del catálogo **Sucursales** (ej. `MTY01`). |
| 6 | `moneda` | Clave de catálogo | Sí | Clave del catálogo **Monedas** (ej. `MXN`). |
| 7 | `actividad` | Clave de catálogo | Sí | Clave del catálogo **Actividades**; determina el sector económico. |
| 8 | `localidad` | Clave de catálogo | Sí | Clave del catálogo **Localidades**. |
| 9 | `garantia` | Clave de catálogo | No | Clave del catálogo **Garantías**; vacío = sin garantía. |
| 10 | `monto_original` | Decimal | Sí | Monto originalmente otorgado. |
| 11 | `saldo_vigente` | Decimal | Sí | Saldo vigente al corte. |
| 12 | `saldo_vencido` | Decimal | Sí | Saldo vencido al corte. |
| 13 | `dias_mora` | Entero | Sí | Días de mora al corte (0 = al corriente). |
| 14 | `plazo_meses` | Entero | Sí | Plazo contratado en meses. |
| 15 | `tasa_anual` | Decimal | Sí | Tasa de interés anual (%). |
| 16 | `fecha_otorgamiento` | Fecha `AAAA-MM-DD` | Sí | Fecha de otorgamiento. |
| 17 | `fecha_vencimiento` | Fecha `AAAA-MM-DD` | Sí | Fecha de vencimiento contractual. |

## Reglas de validación

1. Las claves de catálogo deben existir previamente; los renglones con claves
   inexistentes se **rechazan** y se reportan con número de línea y motivo.
2. La combinación `periodo` + `folio` es única: si se recarga un archivo, los
   créditos del mismo periodo y folio se **reemplazan** (recarga idempotente).
3. Los importes deben ser numéricos; las fechas, válidas en formato ISO.
4. El resultado de cada carga (aceptados, rechazados, errores) queda registrado
   en el historial del proceso de carga.

## Obtención del lay out

La información se extrae del sistema transaccional (core) de la entidad al
cierre de cada mes, con el corte contable de la cartera. El área de sistemas
genera el CSV con las columnas anteriores y el área de riesgos lo carga en el
módulo **Procesos → Carga de información**.
