# Induction Motor Testing — How the Project Works

> Describes the Electron application in this repository (version 2.0.0, ported from the Django app on branch
> `window_graph_modification` in October 2026). The behaviour contract it implements is `PROJECT_SPECIFICATION.md`.

## 1. Summary

A single Electron app with no server, no Python and no internet dependency. The **main process** owns the SQLite database,
the formulas, the `.mdb` reader, the report template and PDF printing. The **renderer** is a sandboxed single-page UI that
can only call named services through one bridged function, `window.bridge.call(name, payload)`.

```
renderer/app.js ──window.bridge.call──▶ preload.js ──ipcRenderer.invoke('api')──▶ main.js handlers
                                                                                 ├─ src/services.js  (motors, tests, imports, users, settings, report data)
                                                                                 │    ├─ src/calc.js    (formulas)
                                                                                 │    ├─ src/report.js  (report HTML)
                                                                                 │    └─ src/db.js      (node:sqlite)
                                                                                 ├─ src/mdb.js       (mdb-reader)
                                                                                 └─ src/pdf.js       (hidden window → printToPDF)
```

## 2. Why these choices

| Concern | Choice | Reason |
|---|---|---|
| Database | `node:sqlite` built into Electron's Node | No native module to rebuild or cross-compile; one file in the user-data folder |
| Access files | `mdb-reader` (pure JS) | Works on every OS with no driver; replaces pyodbc, mdbtools and mdb2csv.exe |
| PDF | `webContents.printToPDF` | Same HTML and CSS as before, rendered by the bundled Chromium; replaces wkhtmltopdf |
| Chart | Chart.js UMD copied into `renderer/vendor` | Same library and config as the Django page; no CDN |
| UI | Vanilla HTML/CSS/JS | No build step, no framework download, small enough to read in one sitting |
| Fonts | System fonts | Nothing to fetch; the report keeps Times New Roman, which Windows ships |

## 3. Runtime flow

1. `main.js` sets up the window, opens `%APPDATA%/Induction Motor Testing/motor-lab.sqlite` (schema created on first run),
   builds the services and registers one IPC channel `api` that dispatches by service name. Every call returns
   `{ ok, data }` or `{ ok: false, error }`, which the preload turns into a resolved value or a thrown `Error`.
2. On first run `services.js` seeds the user `admin` / `admin` (scrypt-hashed).
3. The renderer renders screens from `state`: **login → motors → motor form → workspace → report studio**, plus **settings**.
   Each screen is a template function; `data-action` attributes route clicks and submits to handlers.

## 4. Data model (src/db.js)

`motors` (the InductionMotor row, soft-deleted via `status`), `performance_tests` (7 rows per motor: Routine / Type /
Special flags and `PENDING | COMPLETED | NOT_FOUND`), seven one-to-one result tables keyed by `motor_id`,
`performance_test_parameters` (the 10 load rows), `users`, and `settings` (reports folder, PDF scale, remembered `.mdb` paths).
`mdb_data` columns hold the matched instrument rows as JSON, exactly as the Django JSONField did.

## 5. Status rules

- Create: a ticked test is `PENDING`, an unticked one `NOT_FOUND`. At least one must be ticked.
- Saving a test marks it `COMPLETED`. Editing the motor keeps `COMPLETED` while the test stays ticked, otherwise it drops to
  `PENDING` or `NOT_FOUND`.
- "All completed" means every `PENDING`/`COMPLETED` row is `COMPLETED`.

## 6. Imports and formulas (src/calc.js)

The three instrument tests read the table named `day+month+year` (no leading zeros) from the chosen `.mdb`, filter rows by
the motor serial number (column 1 for No Load and Lock Rotor, column 3 for Performance) and compute with the column maps of
the motor type (`45kw` vs `5kw`). Power factor is the constant 0.89, synchronous speed assumes two poles, efficiency is the
house formula `P_mech / (P_elec + P_mech + P_loss)`, horsepower uses 5252, watts-out is `V·I·√3`. Lock Rotor stores the
average frequency in `speed`. Performance Determination refuses to run until all three resistances are entered, produces
the row-level `mdb_data` for the chart and the 10-row load table for the report. `test/calc.test.js` pins these down.

Two deliberate deviations from the Python: rows whose load is outside the ten buckets are skipped instead of turning into a
"no record for this date" error, and `null` values render blank in the report instead of the word "None". Unbalance (%) is
computed on save as `|R1−R2| + |R1−R3| + |R2−R3|`, which the old page did in browser JavaScript.

## 7. Report and PDF

`src/report.js` is the old `induction_report.html` as a template function with the same markup and class names;
`assets/report/induction_report.css` is the original stylesheet byte for byte. Numbers print with the decimal places of the
Django fields (3, or 2 for nameplate PF and efficiency). Export writes the HTML to a temp file, loads it in a hidden
window and prints A4 with `scale` 0.74 (Settings → Print scale) so the 910 px layout fits like wkhtmltopdf's smart shrinking.
The file is saved as `<customer>-<serial>.pdf` in the reports folder and the path is stored on the motor.

## 8. Tests

```
npm test                 # calc formulas, services end-to-end on an in-memory DB, report HTML
npx electron . --smoke   # launches the real UI against a temp database, drives every screen, exports a PDF, prints SMOKE …
```

## 9. Packaging

`electron-builder` (`npm run dist:win`) produces an offline NSIS installer; `files` in `package.json` lists what ships.
No native modules are involved, so building the Windows installer from macOS or Linux works without a toolchain.
