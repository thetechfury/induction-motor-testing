# Induction Motor Testing

Offline desktop application for the UET Motor Testing Lab (Kala Shah Kaku). It records the standardized tests performed on
three-phase induction motors, computes the derived values, draws the performance curve and prints the fixed two-page PDF
test report. It is a port of the earlier Django application to Electron; every formula, status rule and the report layout are
unchanged (see `PROJECT_SPECIFICATION.md` for the behaviour contract and `PROJECT_WORKING.md` for how this code is organised).

**No internet is needed to install or run it.** All libraries ship inside the installer, the database is a local SQLite file,
fonts are the system's own, and the PDF is produced by the bundled Chromium.

## Run from source

```bash
npm install        # needs internet once, on the developer machine
npm start          # launches the app
npm test           # formulas, services and report rendering
```

First sign-in: user `admin`, password `admin`. Change it under **Settings → Change my password** and add the lab's own users there.

## Build the installer

```bash
npm run dist:win     # dist/Induction Motor Testing Setup 2.0.0.exe  (NSIS, offline installer)
npm run dist:linux   # dist/*.AppImage
```

Copy the installer to the lab PC with a USB drive and run it. Nothing else has to be installed there: no Python, no
wkhtmltopdf, no Microsoft Access driver.

## Where things live on the lab PC

| What | Where |
|---|---|
| Database | `%APPDATA%\Induction Motor Testing\motor-lab.sqlite` |
| PDF reports | `Documents\Motor Testing Reports\<customer>-<serial>.pdf` (change in Settings) |
| Instrument `.mdb` files | Anywhere; chosen per test and remembered |

Back up the database file to keep the motor records.

## Daily flow

1. **Motors** → **New motor**: identification, nameplate, motor type (45 KW or up to 5 KW) and the Routine / Type / Special matrix.
2. **Tests**: the sidebar lists the selected tests. Manual tests are typed in. The three instrument tests (No Load, Lock Rotor,
   Performance Determination) take a test date and the `.mdb` file; **Preview import** shows the computed values before
   **Import, save and mark completed** writes them. Performance Determination needs the three resistances from Electric Resistance first.
3. **Report & curve**: live preview of the report, final remarks, **Export PDF**, and the performance curve with PNG export.

## Project layout

```
main.js              Electron main process: window, IPC dispatch, PDF export, file dialogs
preload.js           exposes window.bridge.call(name, payload) to the page
src/calc.js          the formulas (pure functions, tested)
src/services.js      motors, tests, imports, users, settings, report data
src/db.js            SQLite schema (node:sqlite, no native modules)
src/mdb.js           reads a table of an Access .mdb file (mdb-reader, pure JavaScript)
src/report.js        the report template, unchanged markup and CSS
src/pdf.js           hidden window + printToPDF
renderer/            the UI: index.html, app.css, app.js, vendor/chart.umd.js
assets/report/       report stylesheet and logo
test/                node --test suites and the --smoke UI script
```

## License

[CC0 1.0 (Public Domain)](LICENSE.md)
