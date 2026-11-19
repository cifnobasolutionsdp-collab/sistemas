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

## Modelo S-O-L-I-D-E-Z

El sistema evalúa siete dimensiones de la solidez financiera. Cada indicador
tiene un código con la letra de su dimensión.

| Dimensión | Peso en el índice | Indicadores |
|---|---|---|
| **S** — Salvaguarda de cartera | 20 % | S1 Cobertura de mora > 12 meses (100 %), S2 Cobertura de mora de 1 a 12 meses (≥ 35 %), S3 Saneamiento total de cartera > 12 meses (Sí), S4 Intensidad de castigos, S5 Efectividad en la recuperación de castigos (> 75 %), S6 Respaldo patrimonial al ahorrador (≥ 111 %, SOCAP) |
| **O** — Orden del balance | 15 % | O1 Colocación productiva del activo (70-80 %), O2 Peso de la liquidez (≤ 16 %), O3 Inversiones financieras (≤ 2 %), O4 Inmovilización en inversiones no financieras (0 %), O5 Fondeo con ahorro de socios (70-80 %), O6 Dependencia de fondeo externo (0-5 %), O7 Peso de las aportaciones (10-20 %), O8 Fortaleza patrimonial (≥ 10 %), O9 Fortaleza patrimonial neta de riesgos (≥ 10 %), O10 Apalancamiento (≤ 5 veces, SOFOM) |
| **L** — Liquidez | 15 % | L1 Liquidez disponible para ahorradores (≥ 15 %), L2 Reserva de liquidez (≥ 10 %), L3 Efectivo ocioso (< 1 %) |
| **I** — Ingresos, costos y rentabilidad | 15 % | I1–I4 rendimiento de cartera, liquidez e inversiones vs. tasa empresarial / de mercado, I5–I7 costo del ahorro, del fondeo externo y de las aportaciones, I8 Margen financiero (≥ I9 + I10), I9 Carga operativa (3-10 %), I10 Carga de estimaciones (suficiente para la PCE), I11 Resultados no recurrentes, I12 ROA, I13 ROC (> inflación), I14 Eficiencia operativa (≤ 75 %) |
| **D** — Deterioro y pérdida esperada (IFRS 9) | 20 % | D1 Cartera sana (≥ 90 %), D2 Cartera en vigilancia (≤ 5 %), D3 Cartera deteriorada (≤ 5 %), D4–D6 suficiencia de reservas por etapa, D7 Suficiencia total vs. PCE (≥ 100 %), D8 Cobertura de cartera deteriorada, D9 Costo de riesgo (≤ 3 %), D10 Migración neta a etapas 2 y 3, D11 Capital ajustado por pérdida esperada (≥ 10 %) |
| **E** — Eficiencia de activos | 10 % | E1 Índice de morosidad (≤ 5 %), E2 Activos que no generan ingresos (≤ 5 %), E3 Financiamiento sin costo del activo improductivo (≥ 200 %) |
| **Z** — Zona de crecimiento | 5 % | Z1–Z11 crecimiento de cartera neta, liquidez, inversiones, ahorro, fondeo externo, aportaciones, capital institucional (≥ Z11), capital neto, socios y activo total |

Valores en porcentaje salvo indicación. *I*: flujos anualizados (12 ÷ meses
transcurridos) entre el **saldo promedio** de los cortes del ejercicio
(incluido el cierre anterior). *Z*: crecimiento anualizado contra el cierre del
ejercicio anterior (o el corte previo disponible). Estatus *Alerta*: fuera de
meta por menos de 10 % de la meta.

### Índice SOLIDEZ

Puntaje de 0 a 100 por dimensión: cada indicador evaluado vale 100 si cumple,
50 si está en alerta y 0 si es deficiente (los informativos y los que no
aplican no cuentan). El índice global es el promedio ponderado de las
dimensiones con los pesos de la tabla (si una dimensión no tiene indicadores
evaluables, su peso se redistribuye).

| Puntaje | Calificación |
|---|---|
| ≥ 85 | Sólida |
| 70 – 84 | Estable |
| 50 – 69 | En vigilancia |
| < 50 | Crítica |

Para **SOFOMES** no aplican los indicadores ligados a captación y
aportaciones (S6, O5, O7, I5, I7, L1, L2, Z5, Z7); O8 se calcula con el
capital contable y O6 es informativo. Las metas por omisión son las metas de
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
Los códigos se convirtieron a la nomenclatura S-O-L-I-D-E-Z. Las
estrategias e interrelaciones de la dimensión D (IFRS 9), de O10 y de I14 se
agregaron en `app/monitoreo/estrategias.py`.

## Datos de demostración

```bash
python scripts/seed_monitoreo.py
```

Genera en `data/` balanzas de una SOCAP (tres cortes), sus datos
complementarios y estados financieros de una SOFOM (dos cortes), y los importa.
