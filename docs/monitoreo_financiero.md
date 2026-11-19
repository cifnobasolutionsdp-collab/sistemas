# Sistema de Evaluación y Monitoreo Financiero

Módulo para que las **SOCAPS** y **SOFOMES** importen su **balanza de
comprobación** o sus **estados financieros** y obtengan un monitoreo de
indicadores semejante al archivo de referencia proporcionado, ampliado con
indicadores de **pérdida crediticia esperada bajo IFRS 9** y con un **plan de
acción** que prioriza las estrategias de mejora.

## Flujo

1. **Alta de la entidad** (*Evaluación y Monitoreo Financiero → Entidades y semáforo*): clave,
   nombre, tipo (SOCAP / SOFOM) y nivel de operación.
2. **Importación** (*Importar balanza / estados*), por fecha de corte:
   * **Balanza de comprobación** (CSV, XLSX o XLS). Las cuentas se agrupan en
     rubros con el *mapeo de cuentas*.
   * **Lay out de estados financieros** (`/monitoreo/plantilla/estados.xlsx`):
     Balance General, Estado de Resultados y **Datos complementarios**.
   * Lo habitual: importar la balanza y después sólo la hoja de *Datos
     complementarios* del lay out (morosidad por antigüedad, castigos,
     reservas por etapa, socios, parámetros del periodo).
3. **Tablero**: semáforo de cada indicador (Cumple / Alerta / Deficiente /
   Informativo / N/A), histórico de los últimos cortes, porcentaje de
   indicadores deficientes, ajuste requerido en pesos para alcanzar cada
   meta y sección IFRS 9.
4. **Detalle por indicador**: fórmula, meta, evolución, interrelación directa e
   indirecta (afecta a / es afectado por, coloreadas por estatus) y
   estrategias para mejorarlo.
5. **Plan de acción**: los indicadores deficientes se ordenan por *efecto
   palanca* (cuántos indicadores mejoran al corregirlo, en especial los que
   también están fuera de meta) e identifican las **causas probables**.
   Imprimible a PDF.
6. **Exportación a Excel**: hojas *Indicadores* (histórico con semáforo),
   *Plan de acción*, *IFRS 9* y *Rubros*.

## Balanza de comprobación

| Columna | Obligatoria | Descripción |
|---|---|---|
| `cuenta` | Sí | Número de cuenta (se ignoran guiones, puntos y espacios). |
| `saldo_final` | Sí\* | Saldo al corte. |
| `saldo_deudor`, `saldo_acreedor` | Sí\* | Alternativa a `saldo_final`. |
| `descripcion` | No | Nombre de la cuenta. |
| `rubro` | No | Clave de rubro que asigna la cuenta explícitamente. |
| `tipo` / `afectable` | No | `D`/`detalle` para cuentas de detalle; cualquier otro valor = acumulativa. |

\* Una de las dos opciones.

* **Cuentas de mayor**: se omiten automáticamente para no duplicar saldos
  (código que es prefijo de otra cuenta, o —en catálogos de longitud fija—
  código con ceros a la derecha que agrupa cuentas más específicas). Si su
  catálogo no permite inferirlo, use la columna `tipo`.
* **Convención de signos**: con columnas deudor/acreedor, o con una sola
  columna en la que las cuentas acreedoras (2, 3, 4) vengan en negativo, se
  interpreta como saldo con signo; si no, como saldos según su naturaleza.
* **Balanza no cerrada**: si no hay saldo en *resultado del ejercicio*, se
  calcula como ingresos − gastos de las cuentas de resultados.
* **Validación**: se reporta el descuadre Activo − Pasivo − Capital y las
  cuentas de detalle sin rubro.

### Mapeo de cuentas

Reglas *prefijo → rubro*; gana el prefijo más largo y las reglas propias de la
entidad tienen prioridad sobre las generales. Las reglas generales iniciales
siguen un catálogo de referencia de 4 dígitos (1 Activo, 2 Pasivo, 3 Capital,
4 Ingresos, 5 Gastos) con la cartera clasificada en etapas 1, 2 y 3:

| Prefijo | Rubro | Prefijo | Rubro |
|---|---|---|---|
| 1101 | Caja (liquidez ociosa) | 2101 / 2102 | Depósitos vista / plazo |
| 1102, 1103 | Bancos | 22 | Préstamos bancarios (crédito externo) |
| 1201 | Inversiones corto plazo | 23, 24, 25 | Pasivos sin costo |
| 1202, 1203 | Inversiones largo plazo | 31 | Capital social / aportaciones |
| 1301 / 1302 / 1303 | Cartera etapa 1 / 2 / 3 | 3201, 3204 | Reservas de capital |
| 1304 | Estimación preventiva | 3202 / 3203 | Resultados anteriores / del ejercicio |
| 14 | Cuentas por cobrar | 4101–4104 | Intereses cartera / disponibilidades / inversiones |
| 15 | Bienes adjudicados | 42, 43, 44 | Comisiones / otros ingresos |
| 16 | Activo fijo | 5101–5103 | Intereses depósitos / préstamos / aportaciones |
| 17 | Inversiones permanentes | 52, 53, 54, 55, 56 | Comisiones, estimaciones, gastos de administración, otros, impuestos |
| 18, 19 | Otros activos | | |

**Cada entidad debe ajustar estas reglas a su catálogo de cuentas.** Si su
catálogo sólo distingue cartera *vigente* y *vencida*, mapee la vigente a
etapa 1 y la vencida a etapa 3 (y capture la etapa 2 en datos complementarios
si la conoce).

## Lay out de estados financieros

Columnas `clave` e `importe` (cualquier hoja). Importes positivos según su
naturaleza; el resultado del ejercicio puede ser negativo. El estado de
resultados es **acumulado del 1 de enero a la fecha de corte**. Claves de
parámetros del periodo: `inflacion`, `tasa_mercado`, `tasa_empresarial`
(en porcentaje anual). La importación es parcial: los rubros no incluidos
conservan su valor.

Datos complementarios: `mora_1_12`, `mora_mas_12`, `castigos_ejercicio`,
`castigos_acumulados`, `recuperaciones_acumuladas`, `reserva_etapa1..3`,
`pe_etapa1..3` (PCE propia), `activos_problematicos`, `cxp_30_dias`,
`reserva_liquidez`, `asociados`.

## Indicadores

Valores en porcentaje salvo indicación. *R*: flujos anualizados (12 ÷ meses
transcurridos) entre el **saldo promedio** de los cortes del ejercicio
(incluido el cierre anterior). *S*: crecimiento anualizado contra el cierre del
ejercicio anterior (o el corte previo disponible). Estatus *Alerta*: fuera de
meta por menos de 10 % de la meta.

| Grupo | Indicadores |
|---|---|
| **P** Protección | P1 Estimaciones/mora > 12 m (100 %), P2 Estimaciones netas/mora 1-12 m (≥ 35 %), P3 Depuración completa (Sí), P4 Castigos/cartera promedio, P5 Recuperaciones/castigos acumulados (> 75 %), P6 Solvencia (≥ 111 %, SOCAP) |
| **E** Estructura | E1 Préstamos netos/activo (70-80 %), E2 Inversiones líquidas (≤ 16 %), E3 Inv. financieras (≤ 2 %), E4 Inv. no financieras (0 %), E5 Depósitos (70-80 %), E6 Crédito externo (0-5 %), E7 Aportaciones (10-20 %), E8 Capital institucional (≥ 10 %), E9 Capital institucional neto (≥ 10 %) |
| **R** Rendimientos y costos | R1–R4 rendimientos vs. tasa empresarial / de mercado, R5–R7 costos financieros, R8 Margen bruto (≥ R9 + R10), R9 Gastos operativos (3-10 %), R10 Provisiones (suficientes para la PCE), R11 Otros, R12 ROA, R13 ROC (> inflación) |
| **L** Liquidez | L1 (Inv. líquidas − CxP ≤ 30 d)/depósitos (≥ 15 %), L2 Reserva de liquidez (≥ 10 %), L3 Liquidez ociosa (< 1 %) |
| **A** Activos improductivos | A1 Morosidad (≤ 5 %), A2 Activo improductivo (≤ 5 %), A3 Fondos sin costo/activo improductivo (≥ 200 %) |
| **S** Señales expansivas | S1–S11 crecimiento de cartera, inversiones, depósitos, crédito externo, aportaciones, capital institucional (≥ S11), capital neto, asociados y activo total |
| **I** IFRS 9 | I1–I3 cartera por etapa, I4–I6 suficiencia de reservas por etapa, I7 suficiencia total (EPRC ÷ PCE), I8 cobertura de etapa 3, I9 costo de riesgo, I10 deterioro neto (migración a etapas 2 y 3), I11 capital ajustado por déficit IFRS 9 |
| **K** Solvencia / eficiencia | K1 Apalancamiento (pasivo/capital ≤ 5 veces, SOFOM), K2 Gastos de administración/margen bruto (≤ 75 %) |

Para **SOFOMES** no aplican los indicadores ligados a captación y
aportaciones (P6, E5, E7, R5, R7, L1, L2, S5, S7); E8 se calcula con el
capital contable y E6 es informativo. Las metas por omisión son las metas de
excelencia del archivo de referencia y pueden personalizarse por tipo de
entidad en *Metas de indicadores*.

## IFRS 9 — pérdida crediticia esperada

`PCE = EAD × PD × LGD × factor prospectivo`, por etapa:

* **Etapa 1**: PD a 12 meses (por omisión 3 %).
* **Etapa 2**: PD de vida remanente — incremento significativo del riesgo
  (25 %).
* **Etapa 3**: crédito deteriorado, PD = 100 %.
* **LGD** por omisión 45 %.
* **Factor prospectivo**: promedio ponderado de escenarios (Base 60 % × 1.00,
  Optimista 15 % × 0.85, Pesimista 25 % × 1.35). Se muestra la PCE y el
  déficit de cada escenario (sensibilidad).

Si la entidad reporta su propia PCE (`pe_etapa1..3`) se usa ésa. Si no reporta
la reserva por etapa, la EPRC total se asigna primero a etapa 3, luego a etapa
2 y el remanente a etapa 1. Los parámetros se configuran por entidad y deben
calibrarse con su experiencia de pérdida y la metodología vigente de la CNBV
(NIF C-16 / criterios contables aplicables).

## Fuentes de estrategias e interrelación

Las estrategias y la matriz de interrelación de los indicadores provienen del
archivo de referencia proporcionado (`app/monitoreo/indicadores_base.json`).
En ese archivo las señales expansivas usan la numeración de la hoja
*Explicación* (S1 Activo total … S7 Asociados); se convirtieron a la
numeración S1–S11 de la hoja de indicadores. Las estrategias e
interrelaciones de los indicadores IFRS 9 (I) y de solvencia/eficiencia (K)
se agregaron en `app/monitoreo/estrategias.py`.

## Datos de demostración

```bash
python scripts/seed_monitoreo.py
```

Genera en `data/` balanzas de una SOCAP (tres cortes), sus datos
complementarios y estados financieros de una SOFOM (dos cortes), y los importa.
