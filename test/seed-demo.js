'use strict';
// Seeds demo motors into the app's real database and exports their PDFs. Run: npx electron test/seed-demo.js
const { app } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const { openDb } = require('../src/db');
const { createServices } = require('../src/services');
const { exportPdf } = require('../src/pdf');
const { makeRows } = require('./fixtures/mdb-rows');

app.setName('Induction Motor Testing'); // same userData folder as `npm start`
const ALL = ['electric_resistance_test', 'temperature_rise_test', 'performance_determination_test', 'no_load_test', 'withstand_voltage_ac_test', 'insulation_resistance_test', 'lock_rotor_test'];
const DEMO = [
  ['UET-24-001', 'Pak Elektron Ltd', 'SO-2401', '45kw', 45, ALL, ALL],
  ['UET-24-002', 'Siddiqsons Energy', 'SO-2402', '5kw', 4, ['electric_resistance_test', 'performance_determination_test', 'no_load_test', 'withstand_voltage_ac_test', 'insulation_resistance_test']],
  ['UET-24-003', 'Nishat Mills', 'SO-2403', '45kw', 37, ['electric_resistance_test', 'performance_determination_test', 'no_load_test', 'lock_rotor_test']],
  ['UET-24-004', 'Crescent Steel', 'SO-2404', '45kw', 45, ALL],
  ['UET-24-005', 'Fauji Fertilizer', 'SO-2405', '5kw', 3, ['electric_resistance_test', 'temperature_rise_test', 'performance_determination_test', 'no_load_test', 'insulation_resistance_test']],
  ['UET-24-006', 'Lucky Cement', 'SO-2406', '45kw', 30, ['electric_resistance_test', 'performance_determination_test', 'lock_rotor_test', 'withstand_voltage_ac_test']],
  ['UET-24-007', 'Ittehad Chemicals', 'SO-2407', '5kw', 5, ALL],
  ['UET-24-008', 'Descon Engineering', 'SO-2408', '45kw', 22, ['electric_resistance_test', 'no_load_test', 'withstand_voltage_ac_test', 'insulation_resistance_test']],
  ['UET-24-009', 'Gul Ahmed Textile', 'SO-2409', '45kw', 45, ALL, ['electric_resistance_test', 'temperature_rise_test']], // in progress
  ['UET-24-010', 'Attock Refinery', 'SO-2410', '5kw', 2, ['electric_resistance_test', 'performance_determination_test', 'no_load_test'], []], // not started
];

app.whenReady().then(async () => {
  const userData = app.getPath('userData');
  fs.mkdirSync(userData, { recursive: true });
  const db = openDb(path.join(userData, 'motor-lab.sqlite'));
  let current = {};
  const services = createServices({ db, readMdbTable: async (file) => makeRows(current.serial, current.testType, file.includes('perf') ? 'perf' : file.includes('lock') ? 'lock' : 'noload', current.k) });
  const assets = { css: fs.readFileSync(path.join(__dirname, '../assets/report/induction_report.css'), 'utf8'), logoDataUri: 'data:image/png;base64,' + fs.readFileSync(path.join(__dirname, '../assets/report/logo.png')).toString('base64'), print: true };
  const reportsDir = services['settings.get']().reports_dir || path.join(app.getPath('documents'), 'Motor Testing Reports');
  const out = [];

  for (const [i, [serial, customer, so, testType, power, selected, done = selected]] of DEMO.entries()) {
    if (services['motors.list']({ search: serial }).some((m) => m.serial_number === serial)) { out.push(`${serial}: already exists, skipped`); continue; }
    const k = testType === '45kw' ? power / 45 : power / 5 * 0.18;
    current = { serial, testType, k };
    const kw = testType === '45kw' ? power : power;
    const id = services['motors.create']({ userId: 1, motor: {
      serial_number: serial, customer_name: customer, sales_order_number: so, test_type: testType, power,
      director_cerad: 'Dr. Abdul Rehman', lab_instructor: 'Engr. Sana Malik', tag: `M-${100 + i}`, material: 'Cast iron', frame: testType === '45kw' ? '225M' : '100L',
      mounting: 'B3', drawing: `DRW-${2400 + i}`, enclosure: 'TEFC', duty_cycle: 'S1', design: 'B', insulation_class: 'F', altitude_M: 1000,
      temperature_rise_K: 80, ambient_temperature_C: 40, service_factor: 1.15, voltage: 400, current: Math.round(kw * 1.8), frequency: 50, speed: 2950, p_f: 0.86, efficiency: 93.5,
    }, tests: selected.map((t, j) => ({ test_type: t, routine: j % 3 !== 1, type: j % 3 === 1, special: t === 'lock_rotor_test' })) });

    const manual = {
      electric_resistance_test: { resistance_ohm_1: 0.21 * k + 0.1, resistance_ohm_2: 0.22 * k + 0.1, resistance_ohm_3: 0.205 * k + 0.1, ambient_temperature_C: 24.5, remarks: 'Windings balanced within tolerance.' },
      temperature_rise_test: { voltage: 400, winding: 50, frequency: 68.4, de_bearing: 55.2, nde_bearing: 52.8 },
      withstand_voltage_ac_test: { description: 'Hi-pot 1 min', voltage_kv: 2.0, time_in_seconds: 60, remarks: 'No breakdown observed.' },
      insulation_resistance_test: { description: 'Megger 500 V', voltage: 500, insulation_resistance: 1250, time_in_seconds: 60, ambient_temperature_C: 24.5, humidity_percentage: 48 },
    };
    const imports = {
      no_load_test: ['demo-noload.mdb', { direction_of_rotation: i % 2 ? 'ANTI_CLOCKWISE' : 'CLOCKWISE' }],
      lock_rotor_test: ['demo-lock.mdb', { vibration: 1.8, noise: 72, temperature: 38 }],
      performance_determination_test: ['demo-perf.mdb', { voltage: 400, frequency: 50, nominal_t: Math.round(kw * 1000 / (2 * Math.PI * 2950 / 60)) }],
    };
    for (const t of done) {
      if (manual[t]) services['tests.saveManual']({ motorId: id, test: t, values: manual[t] });
      else { const [file, values] = imports[t]; await services['tests.importSave']({ motorId: id, test: t, dateStr: '2024-03-06', mdbPath: file, values }); }
    }
    if (done.length === selected.length) {
      services['motors.saveRemarks']({ id, remarks: `Motor ${serial} meets the nameplate ratings. Approved for dispatch.` });
      const outPath = path.join(reportsDir, `${customer}-${serial}.pdf`);
      await exportPdf({ html: services['report.html']({ id, assets }), outPath, tmpHtml: path.join(userData, 'report-print.html'), scale: Number(services['settings.get']().pdf_scale) || 0.74 });
      services['report.setLink']({ id, link: outPath });
      out.push(`${serial}: ${done.length}/${selected.length} tests, PDF ${outPath}`);
    } else out.push(`${serial}: ${done.length}/${selected.length} tests saved, no PDF`);
  }
  services['settings.set']({ key: 'mdb_paths', value: '{}' }); // demo file names are not real files
  console.log(out.join('\n'));
  app.quit();
});
