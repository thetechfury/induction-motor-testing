const test = require('node:test');
const assert = require('node:assert/strict');
const { openDb } = require('../src/db');
const { createServices } = require('../src/services');

// 45kw performance rows: [date, hz, volt, serial, rpm, torque, amp, load, c8, c9, c10]
const perfRows = [
  ['d', 50, 400, 'SN-1', 2990, 10, 5, '10%', 0, 0, 0],
  ['d', 50, 400, 'SN-1', 2900, 50, 20, '100%', 0, 0, 0],
];
// no-load rows: [date, serial, amp, volt, hz, rpm]
const noLoadRows = [['d', 'SN-1', 10, 400, 50, 2990], ['d', 'SN-1', 12, 410, 50, 2980]];

function setup() {
  const db = openDb(':memory:');
  const readMdbTable = async (file, table) => {
    if (table !== '632024') throw new Error('missing');
    return file === 'perf.mdb' ? perfRows : noLoadRows;
  };
  const s = createServices({ db, readMdbTable });
  const tests = [
    { test_type: 'electric_resistance_test', routine: true },
    { test_type: 'performance_determination_test', routine: true },
    { test_type: 'no_load_test', type: true },
    { test_type: 'lock_rotor_test', special: true },
  ];
  const motor = { serial_number: 'SN-1', customer_name: 'Acme', sales_order_number: 'SO-9', power: 45, test_type: '45kw', voltage: 400, p_f: 0.85 };
  const id = s['motors.create']({ userId: 1, motor, tests });
  return { s, id };
}

test('default admin login and password change', () => {
  const { s } = setup();
  assert.deepEqual(s['auth.login']({ username: 'admin', password: 'admin' }), { id: 1, username: 'admin' });
  assert.throws(() => s['auth.login']({ username: 'admin', password: 'nope' }), /Wrong username/);
  s['auth.changePassword']({ userId: 1, current: 'admin', next: 'secret1' });
  assert.ok(s['auth.login']({ username: 'admin', password: 'secret1' }));
});

test('create motor: validation, statuses and listing', () => {
  const { s, id } = setup();
  assert.throws(() => s['motors.create']({ motor: { serial_number: 'x', customer_name: 'c', sales_order_number: 'o', power: 1, test_type: '45kw' }, tests: [] }), /at least one test/);
  assert.throws(() => s['motors.create']({ motor: { serial_number: 'x', customer_name: 'c', sales_order_number: 'o', test_type: '45kw' }, tests: [{ test_type: 'no_load_test', routine: 1 }] }), /power/);
  const data = s['motors.get']({ id });
  assert.equal(data.tests.length, 7);
  assert.deepEqual(data.statuses, { electric_resistance_test: 'PENDING', performance_determination_test: 'PENDING', no_load_test: 'PENDING', lock_rotor_test: 'PENDING' });
  assert.equal(data.allCompleted, false);
  const [row] = s['motors.list']({ search: 'sn-' });
  assert.equal(row.total_tests, 4); assert.equal(row.completed_tests, 0); assert.equal(row.perf_completed, 0);
});

test('manual save, import guard, import save, report and chart', async () => {
  const { s, id } = setup();
  await assert.rejects(s['tests.importSave']({ motorId: id, test: 'performance_determination_test', dateStr: '2024-03-06', mdbPath: 'perf.mdb' }), /Resistance 1/);
  const m = s['tests.saveManual']({ motorId: id, test: 'electric_resistance_test', values: { resistance_ohm_1: '0.3', resistance_ohm_2: '0.3', resistance_ohm_3: '0.3', remarks: 'ok' } });
  assert.equal(m.values.ambient_temperature_C, 0);
  assert.equal(s['motors.get']({ id }).statuses.electric_resistance_test, 'COMPLETED');

  await assert.rejects(s['tests.importPreview']({ motorId: id, test: 'no_load_test', dateStr: '2024-01-01', mdbPath: 'nl.mdb' }), /No record found against this date 2024-01-01/);
  const prev = await s['tests.importPreview']({ motorId: id, test: 'no_load_test', dateStr: '2024-03-06', mdbPath: 'nl.mdb' });
  assert.equal(prev.rowCount, 2); assert.ok(Math.abs(prev.values.voltage - 405) < 1e-9);
  assert.equal(s['motors.get']({ id }).statuses.no_load_test, 'PENDING', 'preview must not write');

  const saved = await s['tests.importSave']({ motorId: id, test: 'no_load_test', dateStr: '2024-03-06', mdbPath: 'nl.mdb', values: { direction_of_rotation: 'ANTI_CLOCKWISE' } });
  assert.equal(saved.allCompleted, false);
  const perf = await s['tests.importSave']({ motorId: id, test: 'performance_determination_test', dateStr: '03/06/2024', mdbPath: 'perf.mdb', values: { voltage: 400, frequency: 50, nominal_t: 290 } });
  assert.equal(perf.table.length, 10);
  await s['tests.importSave']({ motorId: id, test: 'lock_rotor_test', dateStr: '2024-03-06', mdbPath: 'nl.mdb', values: { vibration: 1, noise: 2, temperature: 3 } });

  const data = s['motors.get']({ id });
  assert.equal(data.allCompleted, true);
  assert.equal(data.parameters.length, 10);
  assert.equal(data.results.no_load_test.direction_of_rotation, 'ANTI_CLOCKWISE');
  assert.equal(data.results.no_load_test.report_date, '632024');
  assert.deepEqual(data.settings.mdbPaths, { no_load_test: 'nl.mdb', performance_determination_test: 'perf.mdb', lock_rotor_test: 'nl.mdb' });

  const html = s['report.html']({ id, assets: { css: 'body{}', logoDataUri: 'data:,' } });
  assert.match(html, /3\.1\. Electric Resistance/);
  assert.match(html, /3\.2\. Performance Determination/);
  assert.match(html, /3\.3\. No Load/);
  assert.match(html, /4\. Lock Rotor Test/);
  assert.match(html, /5\. Result/);
  assert.match(html, /Resistance \(mOhms\): 0\.300 \/ 0\.300 \/ 0\.300/);
  assert.match(html, /Direction of Rotation: Anti Clockwise/);
  assert.match(html, /<td>Acme<\/td>|Customer:<\/span> Acme/);

  const chart = s['chart.data']({ id });
  assert.deepEqual(chart.series.speed, [2900, 2990]);

  // edit keeps COMPLETED when still ticked, drops to NOT_FOUND when unticked
  s['motors.update']({ id, motor: { ...data.motor }, tests: [{ test_type: 'electric_resistance_test', routine: 1 }, { test_type: 'no_load_test' }, { test_type: 'temperature_rise_test', type: 1 }] });
  const st = s['motors.get']({ id }).statuses;
  assert.equal(st.electric_resistance_test, 'COMPLETED');
  assert.equal(st.temperature_rise_test, 'PENDING');
  assert.equal(st.no_load_test, undefined);
  s['motors.remove']({ id });
  assert.equal(s['motors.list']({}).length, 0);
});
