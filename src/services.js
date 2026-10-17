'use strict';
const crypto = require('node:crypto');
const calc = require('./calc');
const { renderReport } = require('./report');

const TEST_TYPES = [
  'electric_resistance_test', 'temperature_rise_test', 'performance_determination_test', 'no_load_test',
  'withstand_voltage_ac_test', 'insulation_resistance_test', 'lock_rotor_test',
];
const RESULT_TABLE = {
  electric_resistance_test: 'electric_resistance_tests', temperature_rise_test: 'temperature_rise_tests',
  performance_determination_test: 'performance_determination_tests', no_load_test: 'no_load_tests',
  withstand_voltage_ac_test: 'withstand_voltage_ac_tests', insulation_resistance_test: 'insulation_resistance_tests',
  lock_rotor_test: 'lock_rotor_tests',
};
const MOTOR_TEXT = ['serial_number', 'customer_name', 'sales_order_number', 'director_cerad', 'lab_instructor', 'tag',
  'material', 'frame', 'mounting', 'drawing', 'enclosure', 'duty_cycle', 'design', 'insulation_class', 'test_type'];
const MOTOR_INT = ['altitude_M', 'voltage', 'current', 'power', 'frequency', 'speed'];
const MOTOR_DEC = ['temperature_rise_K', 'ambient_temperature_C', 'service_factor', 'p_f', 'efficiency'];
const MOTOR_FIELDS = [...MOTOR_TEXT, ...MOTOR_INT, ...MOTOR_DEC];
const MANUAL = {
  electric_resistance_test: { dec: ['resistance_ohm_1', 'resistance_ohm_2', 'resistance_ohm_3', 'ambient_temperature_C', 'unbalance_percentage'] },
  temperature_rise_test: { dec: ['voltage', 'winding', 'frequency', 'de_bearing', 'nde_bearing'] },
  withstand_voltage_ac_test: { text: ['description'], dec: ['voltage_kv'], int: ['time_in_seconds'] },
  insulation_resistance_test: { text: ['description'], dec: ['voltage', 'insulation_resistance', 'ambient_temperature_C', 'humidity_percentage'], int: ['time_in_seconds'] },
};

const fail = (msg) => { throw new Error(msg); };
const str = (v, max) => {
  const s = v === null || v === undefined ? '' : String(v).trim();
  if (max && s.length > max) fail(`Value "${s.slice(0, 12)}…" is longer than ${max} characters`);
  return s;
};
const optNum = (v) => (v === null || v === undefined || String(v).trim() === '' ? null : Number(v));
// Django: `value if value else Decimal('0.00')` — empty or zero becomes 0.
const numOrZero = (v) => optNum(v) || 0;
const ticked = (t) => !!(t.routine || t.type || t.special);
const todayYmd = () => new Date().toISOString().slice(0, 10);

function hashPassword(password, salt = crypto.randomBytes(16).toString('hex')) {
  return { salt, hash: crypto.scryptSync(password, salt, 64).toString('hex') };
}

function createServices({ db, readMdbTable }) {
  const q = (sql) => db.prepare(sql);
  const one = (sql, ...p) => q(sql).get(...p);
  const all = (sql, ...p) => q(sql).all(...p);
  const run = (sql, ...p) => q(sql).run(...p);
  const setting = (key) => one('SELECT value FROM settings WHERE key = ?', key)?.value ?? null;

  if (!one('SELECT 1 FROM users LIMIT 1')) {
    const { salt, hash } = hashPassword('admin');
    run('INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)', 'admin', salt, hash);
  }

  const motorOr404 = (id) => one('SELECT * FROM motors WHERE id = ?', id) || fail('Motor not found');
  const touch = (id) => run("UPDATE motors SET updated_on = datetime('now') WHERE id = ?", id);
  const statuses = (motorId) => Object.fromEntries(
    all("SELECT test_type, status FROM performance_tests WHERE motor_id = ? AND status IN ('PENDING','COMPLETED')", motorId)
      .map((r) => [r.test_type, r.status]));
  const allCompleted = (motorId) => Object.values(statuses(motorId)).every((s) => s === 'COMPLETED');
  const complete = (motorId, testType) =>
    run("UPDATE performance_tests SET status = 'COMPLETED' WHERE motor_id = ? AND test_type = ?", motorId, testType);
  const ensureResults = (motorId) => {
    for (const t of Object.values(RESULT_TABLE)) run(`INSERT OR IGNORE INTO ${t} (motor_id) VALUES (?)`, motorId);
  };
  const result = (motorId, testType) => one(`SELECT * FROM ${RESULT_TABLE[testType]} WHERE motor_id = ?`, motorId);

  function cleanMotor(input) {
    const m = {};
    for (const f of MOTOR_TEXT) m[f] = str(input[f], f === 'customer_name' ? 100 : f === 'serial_number' || f === 'sales_order_number' ? 20 : 50);
    for (const f of MOTOR_INT) m[f] = optNum(input[f]);
    for (const f of MOTOR_DEC) m[f] = optNum(input[f]);
    for (const f of ['serial_number', 'customer_name', 'sales_order_number']) if (!m[f]) fail(`${f.replace(/_/g, ' ')} is required`);
    if (!['45kw', '5kw'].includes(m.test_type)) fail('Motor type must be 45kw or 5kw');
    if (m.power === null || !Number.isInteger(m.power) || m.power < 0) fail('Rated power (kW) is required and must be a whole number');
    for (const f of [...MOTOR_INT, ...MOTOR_DEC]) if (m[f] !== null && (Number.isNaN(m[f]) || m[f] < 0)) fail(`${f.replace(/_/g, ' ')} must be a positive number`);
    return m;
  }
  function cleanTests(tests) {
    const byType = Object.fromEntries((tests || []).map((t) => [t.test_type, t]));
    const out = TEST_TYPES.map((tt) => ({ test_type: tt, routine: byType[tt]?.routine ? 1 : 0, type: byType[tt]?.type ? 1 : 0, special: byType[tt]?.special ? 1 : 0 }));
    if (!out.some(ticked)) fail('Select at least one test to perform');
    return out;
  }
  function writeResult(motorId, testType, values) {
    ensureResults(motorId);
    const keys = Object.keys(values);
    run(`UPDATE ${RESULT_TABLE[testType]} SET ${keys.map((k) => `${k} = ?`).join(', ')}, updated_on = datetime('now') WHERE motor_id = ?`,
      ...keys.map((k) => values[k]), motorId);
    complete(motorId, testType);
    touch(motorId);
  }

  // ---- .mdb imports (NoLoadFormSaveView, LockRotorFormSave, PerformanceDeterminationFormSave) ----
  async function computeImport({ motorId, test, dateStr, mdbPath }) {
    const motor = motorOr404(motorId);
    if (!mdbPath) fail('Choose the instrument .mdb file first');
    const tableName = calc.formatDate(dateStr) || fail('Enter the test date as YYYY-MM-DD');
    let rows;
    try { rows = await readMdbTable(mdbPath, tableName); } catch (e) { fail(`No record found against this date ${dateStr}`); }
    const notFound = () => fail(`No record found against this serial number ${motor.serial_number}`);
    if (test === 'no_load_test') {
      const r = calc.noLoad(rows, motor.serial_number, motor.test_type) || notFound();
      return { tableName, rowCount: r.rows.length, values: { voltage: r.voltage, current: r.current, power: r.power, frequency: r.frequency, speed: r.speed }, rows: r.rows };
    }
    if (test === 'lock_rotor_test') {
      const r = calc.lockRotor(rows, motor.serial_number, motor.test_type) || notFound();
      return { tableName, rowCount: r.rows.length, values: { voltage: r.voltage, current: r.current, power: r.power, speed: r.speed }, rows: r.rows };
    }
    if (test === 'performance_determination_test') {
      const buckets = calc.alignLoadData(rows, motor.serial_number, motor.test_type);
      if (!calc.hasAnyBucket(buckets)) notFound();
      const er = result(motorId, 'electric_resistance_test') || {};
      ['resistance_ohm_1', 'resistance_ohm_2', 'resistance_ohm_3'].forEach((f, i) => {
        if (!Number(er[f])) fail(`Please fill Resistance ${i + 1} in  Electric Resistance Test`);
      });
      const avgR = (er.resistance_ohm_1 + er.resistance_ohm_2 + er.resistance_ohm_3) / 3;
      const mdbData = calc.extendRows(buckets, avgR, motor.test_type);
      const table = calc.loadTable(buckets, avgR, motor.test_type);
      return { tableName, rowCount: mdbData.length, averageResistance: avgR, table, mdbData, bucketCounts: Object.fromEntries(calc.LOADS.map((k) => [k, buckets[k].length])) };
    }
    return fail('Unknown import test');
  }

  const services = {
    // ---- auth & users ----
    'auth.login': ({ username, password }) => {
      const u = one('SELECT * FROM users WHERE username = ?', str(username));
      if (!u || hashPassword(String(password ?? ''), u.salt).hash !== u.password_hash) fail('Wrong username or password');
      return { id: u.id, username: u.username };
    },
    'auth.changePassword': ({ userId, current, next }) => {
      const u = one('SELECT * FROM users WHERE id = ?', userId) || fail('User not found');
      if (hashPassword(String(current ?? ''), u.salt).hash !== u.password_hash) fail('Current password is wrong');
      if (String(next ?? '').length < 4) fail('New password needs at least 4 characters');
      const { salt, hash } = hashPassword(next);
      run('UPDATE users SET salt = ?, password_hash = ? WHERE id = ?', salt, hash, userId);
      return true;
    },
    'users.list': () => all('SELECT id, username, created_on FROM users ORDER BY username'),
    'users.create': ({ username, password }) => {
      const name = str(username, 50) || fail('Username is required');
      if (String(password ?? '').length < 4) fail('Password needs at least 4 characters');
      if (one('SELECT 1 FROM users WHERE username = ?', name)) fail('That username already exists');
      const { salt, hash } = hashPassword(password);
      return run('INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)', name, salt, hash).lastInsertRowid;
    },
    'users.remove': ({ id }) => {
      if (one('SELECT COUNT(*) AS n FROM users').n <= 1) fail('Keep at least one user');
      run('DELETE FROM users WHERE id = ?', id); return true;
    },

    // ---- motors (InductionMotorListingsView, TestsView, DeleteReportView, Remarks) ----
    'motors.list': ({ search } = {}) => all(`
      SELECT m.id, m.serial_number, m.customer_name, m.sales_order_number, m.test_type, m.power, m.updated_on, m.report_link,
        (SELECT COUNT(*) FROM performance_tests p WHERE p.motor_id = m.id AND p.status IN ('PENDING','COMPLETED')) AS total_tests,
        (SELECT COUNT(*) FROM performance_tests p WHERE p.motor_id = m.id AND p.status = 'COMPLETED') AS completed_tests,
        EXISTS(SELECT 1 FROM performance_tests p WHERE p.motor_id = m.id AND p.test_type = 'performance_determination_test' AND p.status = 'COMPLETED') AS perf_completed
      FROM motors m WHERE m.status = 'ACTIVE' AND (? = '' OR m.serial_number LIKE '%' || ? || '%' COLLATE NOCASE)
      ORDER BY m.updated_on DESC, m.id DESC`, str(search), str(search)),
    'motors.create': ({ userId, motor, tests }) => {
      const m = cleanMotor(motor || {});
      const ts = cleanTests(tests);
      const id = run(`INSERT INTO motors (user_id, ${MOTOR_FIELDS.join(', ')}) VALUES (?${', ?'.repeat(MOTOR_FIELDS.length)})`,
        userId ?? null, ...MOTOR_FIELDS.map((f) => m[f])).lastInsertRowid;
      for (const t of ts) run('INSERT INTO performance_tests (motor_id, test_type, routine, type, special, page_number, status) VALUES (?, ?, ?, ?, ?, 1, ?)',
        id, t.test_type, t.routine, t.type, t.special, ticked(t) ? 'PENDING' : 'NOT_FOUND');
      return Number(id);
    },
    'motors.update': ({ id, motor, tests }) => {
      motorOr404(id);
      const m = cleanMotor(motor || {});
      const ts = cleanTests(tests);
      run(`UPDATE motors SET ${MOTOR_FIELDS.map((f) => `${f} = ?`).join(', ')}, status = 'ACTIVE', updated_on = datetime('now') WHERE id = ?`,
        ...MOTOR_FIELDS.map((f) => m[f]), id);
      for (const t of ts) {
        const existing = one('SELECT status FROM performance_tests WHERE motor_id = ? AND test_type = ?', id, t.test_type)?.status;
        const status = existing === 'COMPLETED' && ticked(t) ? 'COMPLETED' : ticked(t) ? 'PENDING' : 'NOT_FOUND';
        run(`INSERT INTO performance_tests (motor_id, test_type, routine, type, special, page_number, status) VALUES (?, ?, ?, ?, ?, 1, ?)
             ON CONFLICT(motor_id, test_type) DO UPDATE SET routine = excluded.routine, type = excluded.type, special = excluded.special, status = excluded.status`,
          id, t.test_type, t.routine, t.type, t.special, status);
      }
      return true;
    },
    'motors.get': ({ id }) => {
      const motor = one("SELECT * FROM motors WHERE id = ? AND status = 'ACTIVE'", id) || fail('Motor not found');
      ensureResults(id);
      const results = Object.fromEntries(TEST_TYPES.map((tt) => [tt, result(id, tt)]));
      for (const tt of ['performance_determination_test', 'no_load_test', 'lock_rotor_test']) {
        results[tt].mdb_data = results[tt].mdb_data ? JSON.parse(results[tt].mdb_data) : null;
      }
      const st = statuses(id);
      return {
        motor, results, statuses: st,
        tests: all('SELECT test_type, routine, type, special, status FROM performance_tests WHERE motor_id = ? ORDER BY id', id),
        parameters: all('SELECT load, current, slip, speed, efficiency, cos FROM performance_test_parameters WHERE motor_id = ? ORDER BY id', id),
        allCompleted: Object.values(st).every((s) => s === 'COMPLETED'),
        settings: { mdbPaths: JSON.parse(setting('mdb_paths') || '{}') },
      };
    },
    'motors.remove': ({ id }) => { run("UPDATE motors SET status = 'DELETE' WHERE id = ?", id); return true; },
    'motors.saveRemarks': ({ id, remarks }) => {
      motorOr404(id); run("UPDATE motors SET remarks = ?, updated_on = datetime('now') WHERE id = ?", str(remarks, 500), id); return true;
    },

    // ---- manual tests (Electric, Temperature, WithStandVoltage, Insulation *FormSaveView) ----
    'tests.saveManual': ({ motorId, test, values = {} }) => {
      motorOr404(motorId);
      const spec = MANUAL[test] || fail('Unknown manual test');
      const v = { remarks: str(values.remarks, 250) };
      for (const f of spec.dec || []) v[f] = numOrZero(values[f]);
      for (const f of spec.int || []) v[f] = Math.trunc(numOrZero(values[f]));
      for (const f of spec.text || []) v[f] = str(values[f], 50);
      if (test === 'electric_resistance_test') { // computed by the old form's JS: sum of pairwise differences
        const [a, b, c] = [v.resistance_ohm_1, v.resistance_ohm_2, v.resistance_ohm_3];
        v.unbalance_percentage = Number((Math.abs(a - b) + Math.abs(a - c) + Math.abs(b - c)).toFixed(3));
      }
      writeResult(motorId, test, v);
      return { values: v, allCompleted: allCompleted(motorId) };
    },

    // ---- instrument imports ----
    'tests.importPreview': (args) => computeImport(args),
    'tests.importSave': async (args) => {
      const { motorId, test, mdbPath, values = {} } = args;
      const dateStr = test === 'performance_determination_test' && values.is_current_date ? todayYmd() : args.dateStr;
      const r = await computeImport({ ...args, dateStr });
      if (test === 'no_load_test') {
        writeResult(motorId, test, {
          ...r.values, mdb_data: JSON.stringify(r.rows), report_date: r.tableName, reported_date: calc.formatDateToYmd(dateStr),
          direction_of_rotation: values.direction_of_rotation === 'ANTI_CLOCKWISE' ? 'ANTI_CLOCKWISE' : 'CLOCKWISE', remarks: str(values.remarks, 250),
        });
      } else if (test === 'lock_rotor_test') {
        writeResult(motorId, test, {
          ...r.values, vibration: numOrZero(values.vibration), noise: numOrZero(values.noise), temperature: numOrZero(values.temperature),
          mdb_data: JSON.stringify(r.rows), report_date: r.tableName, reported_date: calc.formatDateToYmd(dateStr), remarks: str(values.remarks, 250),
        });
      } else {
        writeResult(motorId, test, {
          voltage: numOrZero(values.voltage), frequency: numOrZero(values.frequency), nominal_t: numOrZero(values.nominal_t),
          is_current_date: values.is_current_date ? 1 : 0, table_name: r.tableName, report_date: dateStr,
          mdb_data: JSON.stringify(r.mdbData), remarks: str(values.remarks, 250),
        });
        run('DELETE FROM performance_test_parameters WHERE motor_id = ?', motorId);
        for (const p of r.table) run('INSERT INTO performance_test_parameters (motor_id, load, current, slip, speed, efficiency, cos) VALUES (?, ?, ?, ?, ?, ?, ?)',
          motorId, p.load, p.current, p.slip, p.speed, p.efficiency, p.cos);
      }
      const paths = JSON.parse(setting('mdb_paths') || '{}');
      paths[test] = mdbPath;
      services['settings.set']({ key: 'mdb_paths', value: JSON.stringify(paths) });
      return { ...r, rows: undefined, mdbData: undefined, allCompleted: allCompleted(motorId) };
    },

    // ---- settings ----
    'settings.get': () => Object.fromEntries(all('SELECT key, value FROM settings').map((r) => [r.key, r.value])),
    'settings.set': ({ key, value }) => {
      run('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value', str(key), value ?? null); return true;
    },

    // ---- report & chart (ReportView, ChartView) ----
    'report.data': ({ id }) => {
      const data = services['motors.get']({ id });
      const completed = data.tests.filter((t) => t.status === 'COMPLETED');
      return { ...data, completed, hasLockRotor: completed.some((t) => t.test_type === 'lock_rotor_test') };
    },
    'report.html': ({ id, assets }) => renderReport(services['report.data']({ id }), assets),
    'report.setLink': ({ id, link }) => { run('UPDATE motors SET report_link = ? WHERE id = ?', link, id); return true; },
    'chart.data': ({ id }) => {
      const { motor, results } = services['motors.get']({ id });
      return { serial: motor.serial_number, series: calc.chartSeries(results.performance_determination_test.mdb_data, motor.test_type) };
    },
  };
  return services;
}

module.exports = { createServices, TEST_TYPES, hashPassword };
