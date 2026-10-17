# Induction Motor Testing — Project Specification & Rewrite Requirements

> **Purpose of this document.** A complete, implementation-independent specification of the Induction Motor Testing application, written so the system can be **re-architected on a new tech stack** without losing any behaviour. Every calculation, data mapping, flow, and report layout is captured verbatim from the working code so the new build can reproduce results **bit-for-bit**.
>
> **Source of truth.** This spec is reverse-engineered from the git branch **`window_graph_modification`** (tip `dc6fcb8`, 2024-05-30) — the most recent, most complete implementation. The current `main` branch is only an Electron "quick-start" scaffold (a leftover `books` CRUD template) and does **not** contain the motor-testing logic. All file references below point at `window_graph_modification`.
>
> **Current stack (being replaced):** Python 3 · Django 5.0.2 · SQLite · `pdfkit` + `wkhtmltopdf` · `pyodbc`/`mdb-parser` for MS-Access `.mdb` ingestion · Chart.js + html2canvas · Bootstrap 5 · jQuery. Optionally wrapped in Electron for desktop.

---

## 1. Product Overview

The application is a **laboratory information system for a university motor-testing lab** (University of Engineering & Technology, Motor Testing Lab, Kala Shah Kaku). It records the results of standardized electrical tests performed on **three-phase induction motors**, computes derived performance metrics, plots performance curves, and produces a formal **2-page PDF test report** per motor.

### 1.1 Core capabilities
1. **Authentication** — staff log in; every motor record is owned by a user.
2. **Motor registration** — create a motor record (identification + nameplate ratings) and select which of 7 tests apply (as Routine / Type / Special).
3. **Test data entry** — per motor, enter results for each selected test. Some tests are **manual entry**; three are **ingested from MS-Access `.mdb` instrument files** and auto-averaged/computed.
4. **Calculations** — compute efficiency, slip, synchronous speed, horsepower, watts-out, power, average resistance, etc.
5. **Performance curve chart** — plot Torque / Amperes / Efficiency / Horsepower / Watts-out against Speed (RPM); downloadable as PNG.
6. **PDF report** — render a fixed 2-page report and save it to disk.
7. **Listing / search / soft-delete** of motor records.

### 1.2 Two motor "test types" (critical global switch)
Each motor has `test_type ∈ {'45kw', '5kw'}` ("45KW" vs "Up to 5KW"). **This switch changes which columns are read from the instrument `.mdb` files** (see §6). It does not change the formulas, only the column mapping. Every ingestion routine branches on `motor.test_type == '45kw'`.

---

## 2. Domain Model

All monetary/measurement fields are `Decimal` unless noted. Source: `motor_testing/models.py`.

### 2.1 `InductionMotor` (the aggregate root)
One row per motor under test. Fields:

| Field | Type | Notes |
|---|---|---|
| `user` | FK → User | owner (CASCADE) |
| `serial_number` | char(20) | **key used to filter `.mdb` rows** |
| `customer_name` | char(100) | |
| `sales_order_number` | char(20) | |
| `director_cerad` | char(50) | signatory on report |
| `lab_instructor` | char(50) | signatory on report |
| `tag`, `material`, `frame`, `mounting`, `drawing`, `enclosure`, `duty_cycle`, `design`, `insulation_class` | char(50) | "1. Motor Identification" block |
| `altitude_M` | uint | metres |
| `temperature_rise_K` | dec(6,3) | ≥0 |
| `ambient_temperature_C` | dec(6,3) | ≥0 |
| `service_factor` | dec(5,3) | ≥0 |
| `voltage` | uint | nameplate |
| `current` | uint | nameplate |
| `power` | uint | **rated power (kW); required** |
| `frequency` | uint | nameplate Hz |
| `speed` | uint | nameplate rpm |
| `p_f` | dec(5,2) | nameplate power factor |
| `efficiency` | dec(5,2) | nameplate efficiency |
| `status` | `ACTIVE` / `DELETE` | soft-delete flag (default ACTIVE) |
| `report_link` | char(50) | filesystem path to generated PDF |
| `remarks` | char(500) | final remarks |
| `test_type` | `45kw` / `5kw` | **global column-mapping switch** |
| `created_on`, `updated_on` | datetime | auto timestamps |

### 2.2 `PerformanceTest` (test selection / status per motor)
Join row: which of the 7 tests apply to a motor and their completion status.

- `motor` FK → InductionMotor
- `test_type` ∈ the **7 test keys** below
- `routine`, `type`, `special` : nullable booleans (checkbox matrix on the report)
- `page_number` : int (default 1)
- `status` ∈ `PENDING` / `COMPLETED` / `NOT_FOUND`

**The 7 test keys** (`PERFORMANCE_TEST_CHOICES`):
`electric_resistance_test`, `temperature_rise_test`, `performance_determination_test`, `no_load_test`, `withstand_voltage_ac_test`, `insulation_resistance_test`, `lock_rotor_test`.

Status rule (on save): if none of routine/type/special is ticked → `NOT_FOUND`; if any ticked → `PENDING`; when its data form is saved → `COMPLETED`.

### 2.3 The 7 test result tables
Each is a `OneToOne` → `InductionMotor` (so exactly one result row per motor per test), created lazily via `get_or_create` when the Tests screen is opened.

**(1) `ElectricResistanceTest`** — `3.1`
- `resistance_ohm_1/2/3` dec(6,3) — the three phase-winding resistances (milliohms in the report label)
- `ambient_temperature_C` dec(6,3)
- `unbalance_percentage` dec(6,3) — displayed read-only
- `remarks` text(250)
- **Feeds Performance Determination:** average resistance `R̄ = (R1+R2+R3)/3` is consumed there for copper-loss calc. Performance Determination **refuses to run** if any of R1/R2/R3 is empty.

**(2) `TemperatureRiseTest`** — `3.2` (all manual entry)
- `voltage`, `winding`, `frequency`, `de_bearing`, `nde_bearing` dec(6,3), `remarks`
- ⚠️ **Report label/field mismatch to preserve or fix deliberately:** in `induction_report.html` the *Frequency* cell shows `...winding` and the *Winding (Resistance Method)* cell shows `...frequency`. The stored fields and the displayed labels are crossed. Decide during rewrite whether this is a bug to fix or intended.

**(3) `PerformanceDeterminationTest`** — `3.3` (**.mdb-ingested + computed**)
- `voltage`, `frequency`, `nominal_t` (nominal torque) dec — manual header inputs
- `is_current_date` bool, `test_date` date, `report_date` date, `table_name` char(20)
- `mdb_data` JSON — the **row-level computed dataset** used by the chart
- `remarks`
- Has many `PerformanceTestParameters` (the 10-row load table).

**(3a) `PerformanceTestParameters`** — one row per load bucket
- FK → PerformanceDeterminationTest
- `load` (10,20,…,100 %), `current`, `slip`, `speed`, `efficiency`, `cos` — all dec(10,3)

**(4) `NoLoadTest`** — `3.4` (**.mdb-ingested + computed**)
- `voltage`, `current`, `power`, `frequency`, `speed` dec, `direction_of_rotation` ∈ CLOCKWISE/ANTI_CLOCKWISE
- `report_date` char, `reported_date` date, `mdb_data` JSON, `remarks`

**(5) `WithstandVoltageACTest`** — `3.5` (manual)
- `description`, `voltage_kv` dec(6,3), `time_in_seconds` uint, `remarks`

**(6) `InsulationResistanceTest`** — `3.6` (manual)
- `description`, `voltage`, `insulation_resistance`, `time_in_seconds`, `ambient_temperature_C`, `humidity_percentage`, `remarks`

**(7) `LockRotorTest`** — `3.7` (**.mdb-ingested + computed**)
- `vibration`, `noise`, `temperature` — manual
- `speed`, `voltage`, `current`, `power` — computed from `.mdb`
- `report_date`, `reported_date`, `mdb_data`, `remarks`
- ⚠️ **Quirk to preserve:** the `speed` column actually stores **average frequency (Hz)**, not RPM (see §5.2). The report even labels this row "Frequency (Hz)".

### 2.4 `Configuration` (singleton — file locations)
Holds the **absolute paths to the three `.mdb` instrument files**:
- `no_load_test`, `performance_determination`, `lock_rotor_test` (char(100) each).
Read as `Configuration.objects.all().first()`. In the rewrite this should become proper per-test file selection / upload rather than a single global config row.

---

## 3. Global Constants & Units

| Constant | Value | Where | Meaning |
|---|---|---|---|
| `POWER_FACTOR` | **0.89** | `settings.POWER_FACTOR` | **Fixed assumed cos φ** used everywhere power is computed and stored as `cos` in the load table. The app does **not** compute PF from measurements (the PF formula exists in code but is commented out). |
| `√3` | `math.sqrt(3)` ≈ 1.7320508 | views | three-phase line factor |
| HP divisor | **5252** | views | `hp = torque·rpm / 5252` |
| Synchronous-speed pole term | **/2** | views | `ns = f·120 / 2` ⇒ assumes a **2-pole** machine |

**Units as used in the code / report:**
- Voltage V, Current A, Power W (report converts lock-rotor power to kW via `power/1000`), Frequency Hz, Speed RPM.
- Torque: chart axis labels it **`Torque[lb.in]`**; nominal torque field labelled `N.m`. (Unit inconsistency — see §9.)
- Horsepower axis: raw `torque·rpm/5252`.
- Resistance: stored plain; report labels it **mΩ**.

> ⚠️ The commented-out true power-factor formula appears repeatedly:
> `power_factor = (motor_power·1000) / (√3 · V · I)`. It is **never used** — `POWER_FACTOR = 0.89` is used instead. Decide in the rewrite whether to compute real PF or keep the constant.

---

## 4. Test Data Sources

| Test | Data source | Entry mode |
|---|---|---|
| Electric Resistance | user | manual |
| Temperature Rise | user | manual |
| Withstand Voltage AC | user | manual |
| Insulation Resistance | user | manual |
| **No Load** | `.mdb` file (Configuration.no_load_test) | ingested + averaged |
| **Lock Rotor** | `.mdb` file (Configuration.lock_rotor_test) | ingested + averaged |
| **Performance Determination** | `.mdb` file (Configuration.performance_determination) | ingested + per-load computed |

The three ingested tests all follow the same pattern: the user picks a **date**; the app opens the corresponding **table inside the `.mdb`** (table name = date, see §6.2), filters rows by the motor's **serial number**, then averages/computes.

---

## 5. Calculations — EXACT specification

> These formulas must be reproduced **exactly**, including the ordering, the averaging denominators, and the quirks. Line numbers reference `motor_testing/views.py` on `window_graph_modification`.

### 5.1 No-Load Test (`NoLoadFormSaveView`, lines 359–450)
Input: all `.mdb` rows whose column `[1] == serial_number`.

For each matching row, accumulate:
```
sum_rpm      += row[5]                      # both test types
if test_type == '45kw':
    sum_frequency_hertz += row[4]
    sum_volt            += row[3]
    sum_current_amp     += row[2]
else:  # '5kw'
    sum_frequency_hertz += row[8]
    sum_volt            += row[7]
    sum_current_amp     += row[6]
```
Then (n = number of matching rows):
```
avg_rpm            = sum_rpm            / n
avg_frequency_hertz= sum_frequency_hertz/ n
avg_volt           = sum_volt           / n
avg_current_amp    = sum_current_amp    / n

power = avg_volt · avg_current_amp · POWER_FACTOR · √3      # 3-phase apparent→"power" with fixed PF
```
Persist: `voltage=avg_volt`, `current=avg_current_amp`, `power=power`, `frequency=avg_frequency_hertz`, `speed=avg_rpm`, `mdb_data=filtered rows`, `direction_of_rotation` (from form). Empty → `Decimal('0.00')`.

### 5.2 Lock-Rotor Test (`LockRotorFormSave`, lines 533–625)
Input: `.mdb` rows where `[1] == serial_number`.
```
if test_type == '45kw':
    sum_current_amp     += row[2]
    sum_volt            += row[3]
    sum_frequency_hertz += row[4]
else:  # '5kw'
    sum_current_amp     += row[5]
    sum_volt            += row[6]
    sum_frequency_hertz += row[7]

avg_frequency_hertz = sum_frequency_hertz / n
avg_current_amp     = sum_current_amp     / n
avg_volt            = sum_volt            / n

power = avg_volt · avg_current_amp · POWER_FACTOR · √3
```
Persist: `current=avg_current_amp`, `voltage=avg_volt`, `power=power`, **`speed = avg_frequency_hertz`** (⚠️ frequency stored in the speed field — intentional per the report which labels it "Frequency (Hz)"), plus manual `vibration`, `noise`, `temperature`.

### 5.3 Electric Resistance — average resistance
```
R̄ = (resistance_ohm_1 + resistance_ohm_2 + resistance_ohm_3) / 3
```
Used only by Performance Determination. Guard: all three must be non-empty or Performance Determination returns HTTP 400 with a "Please fill Resistance N" message.

### 5.4 Performance Determination (`PerformanceDeterminationFormSave`, lines 628–941)
This is the most complex flow. It produces **two** outputs:
- **(A) row-level `mdb_data`** — per raw sample, extended with hp/watts/efficiency, used by the chart.
- **(B) `PerformanceTestParameters`** — 10 aggregated rows (one per 10 % load bucket), used by the PDF table.

#### Column mapping (per raw `.mdb` row)
| Quantity | 45kw index | 5kw index |
|---|---|---|
| serial_number (filter) | `[3]` | `[3]` |
| load % (bucket key) | `[7]` | `[7]` |
| speed_rpm | `[4]` | `[4]` |
| torque | `[5]` | `[5]` |
| voltage | `[2]` | `[10]` |
| current | `[6]` | `[8]` |
| frequency (Hz) | `[1]` | `[9]` |

Rows are bucketed by `load %` (string like `"10%"` → stripped to `"10"`) into the 10 buckets `10,20,…,100`. Only rows with non-zero voltage, torque, speed, current are kept.

#### (A) Row-level metrics — `perform_calculation_and_extend_determine_data_list` (835–861)
For each kept raw row (using `R̄` from §5.3):
```
mechanical_power = torque · speed_rpm
losses           = R̄ · current²                      # I²R copper loss
electrical_power = current · voltage
efficiency (%)   = mechanical_power
                   / (electrical_power + mechanical_power + losses) · 100
horsepower       = (torque · speed_rpm) / 5252
watts_output     = voltage · current · √3
```
Each row is **appended** with `[horsepower, watts_output, efficiency]`, landing at indices **`[11]`, `[12]`, `[13]`**. The extended rows are de-duplicated (`set` of tuples) and stored in `mdb_data`.

> ⚠️ De-dup via `set()` **loses row order**; the chart re-sorts by speed afterwards (§7). Preserve that behaviour.

#### (B) Aggregated per-load rows — `create_performance_determination_obj` (884–941)
For each load bucket, over the rows in that bucket:
```
speed_rpm_sum += row[4]                       # every row
torque_sum    += row[5]
if test_type == '45kw':
    if row[6] > prev_current:                 # only count *increasing* current samples
        current_sum += row[6]; current_count += 1
    voltage_sum += row[2]
    hertz_sum   += row[1]
else:  # '5kw'
    current_count += 1
    current_sum += row[8]
    voltage_sum += row[10]
    hertz_sum   += row[9]

m = len(rows in bucket)
avg_hertz   = hertz_sum   / m
avg_current = current_sum / current_count      # ⚠️ NB: divided by current_count, not m
avg_speed   = speed_rpm_sum / m
avg_voltage = voltage_sum / m
avg_torque  = torque_sum  / m

ns               = (avg_hertz · 120) / 2       # synchronous speed, assumes 2 poles
mechanical_power = avg_torque · avg_speed
losses           = R̄ · avg_current²
electrical_power = avg_current · avg_voltage
```
Stored per load bucket:
```
load       = 10 | 20 | … | 100
current    = avg_current
slip (%)   = ((ns − avg_speed) / ns) · 100
speed      = avg_speed
efficiency = mechanical_power / (electrical_power + mechanical_power + losses) · 100
cos        = POWER_FACTOR                       # constant 0.89
```
If a bucket has no valid data, the row is filled with the zero-defaults from the `performancetest` template dict.

> ⚠️ Two quirks to preserve or consciously fix:
> 1. **45kw current averaging** only sums samples where current is strictly increasing vs the previous sample (`row[6] > prev_current`) and divides by that count — a monotonic-ramp assumption. 5kw sums all and divides by count. This asymmetry is deliberate in the code.
> 2. `prev_current`/`prev_rpm` are carried across buckets (seeded `prev_current=0`, `prev_rpm=9999`) but `prev_rpm` is effectively unused (the rpm-filter is commented out).

### 5.5 Efficiency formula — note
The efficiency definition used throughout is:
```
η = P_mech / (P_elec + P_mech + P_losses) · 100
```
where `P_mech = torque·speed`, `P_elec = V·I`, `P_losses = R̄·I²`. This is the project's **house formula** — reproduce it exactly even though it differs from a textbook `η = P_out/P_in`. Do not "correct" it silently.

---

## 6. Instrument `.mdb` Ingestion

### 6.1 Reader (`read_mdb_table`, lines 1130–1163)
Cross-platform table read of an MS-Access database:
- **Windows:** `pyodbc` with `DRIVER={Microsoft Access Driver (*.mdb, *.accdb)}`, `SELECT * FROM {table_name}`. Date-typed first column is stringified.
- **Linux:** `mdb_parser.MDBTable(file_path, table)`; first appended row is the column header list.
- Other OS: returns empty.

There is also `mdb_to_csv_conversion` shelling out to a Windows-only `mdb2csv.exe` (`MDB_TO_CSV_EXE_LOCATION`) — a legacy path.

### 6.2 Table-name = date (`format_date`, 944–963)
The user picks a date; the **table inside the `.mdb` is named by that date** as `DDMMYYYY` **with leading zeros stripped** (day then month then year: `2024-03-06` → `"632024"`; `03/06/2024` parsed `%m/%d/%Y`). Accepts `MM/DD/YYYY` or `YYYY-MM-DD` input. `format_date_to_ymd` normalizes to `YYYY-MM-DD` for storage in `reported_date`.

### 6.3 Error contract
- Table/date not found → HTTP 400 `{"error": "No record found against this date <d>"}`.
- No rows for that serial → HTTP 400 `{"error": "No record found against this serial number <s>"}`.

> **Rewrite guidance:** the `.mdb` + Access-driver dependency is the least portable part of the system. Options: (a) keep `.mdb` but ingest via a portable parser; (b) migrate instruments to export CSV/Parquet; (c) accept file upload per test rather than a fixed configured path. The **column indices in §5 are schema contracts** for the instrument export — carry them forward or re-map explicitly.

---

## 7. Performance Curve Chart (`ChartView` / `TestChartView`, 995–1105)

- Loads `PerformanceDeterminationTest.mdb_data` (the extended row-level dataset).
- **Sorts rows ascending by speed** (`row[4]`) via bubble sort (order was lost by the §5.4A `set()` de-dup).
- Extracts series: `speed[4]`, `torque[5]`, `current` (`[6]` for 45kw else `[8]`), `horsepower[11]`, `watts_out[12]`, `efficiency[13]`.
- Renders a **Chart.js multi-axis line chart** (`graph.html`): X = Speed [RPM] (fixed label ticks 1500…3000 step 100), five Y-axes — Torque, Amperes, Efficiency, Horsepower, Watts-out.
- **Download as PNG:** `html2canvas` captures `#chart_div` → `"{serial}-motor-chart.png"`.
- `TestChartView` is a near-duplicate rendering `graph-test.html` (a test/preview variant).

> Note: `static/assets/js/chart.js` is the Google Charts loader library (vendored, minified) and is unrelated to the actual chart, which is drawn inline with Chart.js in `graph.html`.

---

## 8. PDF Report Generation

### 8.1 Primary path (`GeneratePDF`, 254–266) — used in production
```
config = pdfkit.configuration(wkhtmltopdf = WK_HTML_TO_PDF_PATH)   # /usr/local/bin/wkhtmltopdf
report_url  = absolute URL of report/<id>          # renders induction_report.html
report_link = ./generatedReports/{customer_name}-{serial_number}.pdf
pdfkit.from_url(report_url, report_link, configuration=config)
InductionMotor.report_link = report_link           # persisted
```
Response: the saved PDF streamed back inline as `{serial}-motor-report.pdf`.

### 8.2 Secondary path (`html_to_pdf.py`) — present but not wired into the main flow
Uses `xhtml2pdf` (`pisa`) rendering a template to `BytesIO`, encoding HTML as `ISO-8859-1`. Kept as an alternative renderer; the URL-based `wkhtmltopdf` path is what the "PDF" button calls.

### 8.3 Report layout (`templates/induction_report.html`) — 2 fixed pages
The report is a precise fixed layout (styled by `assets/css/induction_report.css`). Reproduce section-for-section:

**Header (both pages):** lab logo image, title "Test Report — Three Phase Induction Motor", motor serial number, "University of Engineering Technology / Motor Testing Lab", address line.

**Page 1**
1. **Customer / Sales Order** line.
2. **§1 Motor Identification** — a table of TAG, Motor Power (shows `test_type`), Material, Enclosure, Insulation Class, Frame, Altitude, Temperature Rise, Mounting, Duty Cycle, Ambient Temp, Drawing, Design, Service Factor. Then a **nameplate table**: Voltage / Current / Power(kW) / Freq / Speed / P.F. / Eff.
3. **§2 Performed Tests** — a 7-row matrix; each of the 7 tests shows `X`/`-` in the Routine / Type / Special columns based on the `PerformanceTest` booleans.
4. **§3 Tests** — only the **COMPLETED** tests render, numbered `3.{loop counter}`:
   - 3.x Electric Resistance — R1/R2/R3, ambient °C, unbalance %.
   - 3.x Temperature Rise — Voltage, Frequency, Winding, DE/NDE bearing (⚠️ label/field crossing, §2.3).
   - 3.x Performance Determination — header (Voltage/Freq/Nominal T) + the **10-row load table**: Load% / Current / Slip% / Speed / Efficiency / Cos Ø.
   - 3.x No Load — Voltage/Current/Power(W)/Frequency/Speed/Direction.
   - 3.x Withstand Voltage AC — Description/Voltage(kV)/Time(s).
   - 3.x Insulation Resistance — Description/Voltage/Insulation Res(MΩ)/Time + ambient°C, humidity%.
5. **Footer** — confidentiality notice + "Report issued on {updated_on}". "Page 1 of 2".

**Page 2**
6. **§4 Lock Rotor Test** (only if selected) — table: Voltage / **Frequency(Hz) ← the `speed` field** / Current / Power(kW = power/1000) / Vibration / Noise / Temperature.
7. **§5 (or §4) Result** — "Final Remarks" plus each test's remarks (only non-empty ones).
8. **Signature footer** — "UET TEST REPORT" / Customer; Director Cerad, Lab Instructor, Inspector; issue date. "Page 2 of 2".

> The section numbering shifts (Result is §5 when Lock Rotor is present, else §4) — preserve.

---

## 9. Known Quirks / Decisions for the Rewrite

These are behaviours found in the current code. For each, decide **preserve** vs **fix** — but do it consciously, not by accident.

1. **Power factor is a hard-coded constant `0.89`**, not measured. The real-PF formula is present but commented out. Reported `cos Ø` is always 0.89.
2. **Efficiency uses the house formula** `P_mech/(P_elec+P_mech+P_losses)` (§5.5), not `P_out/P_in`.
3. **Synchronous speed assumes 2 poles** (`ns = f·120/2`). Multi-pole motors would be wrong — consider making pole-count a motor attribute.
4. **Lock-rotor `speed` field stores frequency (Hz)**, not RPM (§5.2).
5. **Temperature-Rise report labels are crossed** with the stored fields (§2.3).
6. **45kw performance current** is averaged only over strictly-increasing samples and divided by that count, not the row count (§5.4B).
7. **`mdb_data` de-dup with `set()` loses ordering**; the chart compensates by re-sorting on speed.
8. **Torque units are inconsistent** — chart axis says `lb.in`, nominal-torque field says `N.m`, HP uses the imperial 5252 constant (valid for lb·ft·rpm). Pin down the real unit during rewrite.
9. **`.mdb` ingestion is platform-fragile** (Windows Access driver / Linux mdbtools / nothing elsewhere) and reads a **fixed configured file path** with **date-named tables** and **positional column indices** that differ per test and per test_type (§6, §5). This is the top rewrite risk — formalize the instrument data contract.
10. **`Configuration` is a global singleton** holding three file paths — replace with per-test file selection/upload.
11. **Duplicated import block** in `urls.py` and a **near-duplicate `ChartView`/`TestChartView`** — consolidate.
12. **Security**: `DEBUG=True`, `SECRET_KEY` committed, `ALLOWED_HOSTS=['*']`. Must be fixed for any non-desktop deployment.

---

## 10. Application Flows (routes → behaviour)

Source: `motor_testing/urls.py`, `core_settings/urls.py`.

| Route | View | Behaviour |
|---|---|---|
| `/accounts/login/` | Django `LoginView` (custom form) | staff login |
| `/logout/` | `LogoutView` | logout |
| `/home/` | `InductionMotorListingsView` | list ACTIVE motors (paginate 10, newest first); search by serial (`?search=`); "graph" button shown only when Performance Determination is COMPLETED; **create motor** via modal: `InitialForm` + a formset of 7 `PerformanceTestForm` (routine/type/special checkboxes). Requires ≥1 test ticked. |
| `/tests/<pk>` | `TestsView` | lazily `get_or_create` all 7 result rows; render entry forms only for **selected** tests; edit motor identification; save each test independently. |
| `/electric-form/<id>` … `/Lock-rotor-form/<id>` | 7 `*FormSaveView` | **AJAX** endpoints; each validates/computes, saves, marks the `PerformanceTest` COMPLETED, returns `JsonResponse` incl. `all_test_completed`. The 3 ingested tests return HTTP 400 on missing date/serial. |
| `/report/<id>` | `ReportView` | render `induction_report.html` (COMPLETED tests + load-table parameters + lock-rotor flag). |
| `/report/<id>/delete` | `DeleteReportView` | **soft delete** (`status=DELETE`). |
| `/pdf/<id>` | `GeneratePDF` | wkhtmltopdf → save to `generatedReports/` → stream PDF (§8). |
| `/chart/<id>` | `ChartView` | performance curve chart (§7). |
| `/test-chart/<id>` | `TestChartView` | chart preview variant. |
| `/remarks/<id>` | `Remarks` | AJAX save of motor-level final remarks. |

**Motor lifecycle:** create (home modal) → open Tests → fill each selected test (manual or via `.mdb` date+serial) → each save flips status PENDING→COMPLETED → when all COMPLETED, view Report → Generate PDF / view Chart.

---

## 11. Non-Functional / Deployment Notes

- **Auth:** Django users; `LOGIN_REDIRECT_URL=home`. Rebuild with real user management + roles (lab instructor vs director vs inspector map to report signatories).
- **Storage:** SQLite (`db.sqlite3`) + generated PDFs on disk in `generatedReports/` + instrument `.mdb` files at configured paths + `media/` uploads.
- **Desktop packaging:** historically wrapped with Electron (`main` branch scaffold, `launch_expense_tracker.bat`). If the rewrite stays desktop, the `.mdb`/wkhtmltopdf native deps must ship with the bundle.
- **Third-party runtime deps to replace/port:** `wkhtmltopdf` binary, MS-Access ODBC driver or mdbtools, `mdb2csv.exe`, Chart.js, html2canvas, Bootstrap 5, jQuery.
- **`requirements.txt` (current):** `django==5.0.2`, `django-pdfkit==0.3.1`, `mdbtools==0.3.14`, `mdb-parser==0.0.3`, `pyodbc==5.1.0`. (Note: `xhtml2pdf`/`pdfkit`/`Chart.js` are also used but not all pinned here.)

---

## 12. Rewrite Checklist (must-reproduce)

- [ ] Domain model: `InductionMotor` + 7 one-to-one test tables + `PerformanceTest` selection matrix + `PerformanceTestParameters` (10 load rows) + `Configuration`.
- [ ] The **`45kw` vs `5kw` column-mapping switch** for all 3 ingested tests (§5, §6).
- [ ] No-Load averaging + `power = V·I·0.89·√3` (§5.1).
- [ ] Lock-Rotor averaging + `power`, with **frequency stored in `speed`** (§5.2).
- [ ] Average resistance guard + Performance Determination (row-level **and** per-load aggregation) with exact efficiency, slip (`ns=f·120/2`), hp (`/5252`), watts-out (`V·I·√3`) formulas and the 45kw increasing-current averaging rule (§5.3–5.4).
- [ ] `.mdb` ingestion: date→table-name `DDMMYYYY` (leading zeros stripped), serial filter, cross-platform read, HTTP 400 error contracts (§6).
- [ ] Chart: speed-sorted multi-axis curve + PNG download (§7).
- [ ] PDF: 2-page fixed layout, COMPLETED-only test sections, X/- selection matrix, load table, section-number shift, signatories (§8).
- [ ] Flows/routes and PENDING→COMPLETED status transitions (§10).
- [ ] Consciously decide each quirk in §9.

---

*Generated as a reverse-engineered spec from branch `window_graph_modification`. Cross-check the exact column indices against your real instrument `.mdb` export before relying on them — they are positional and per-test.*
