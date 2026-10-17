const test = require('node:test');
const assert = require('node:assert/strict');
const calc = require('../src/calc');

const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test('formatDate strips leading zeros, both input formats', () => {
  assert.equal(calc.formatDate('2024-03-06'), '632024');
  assert.equal(calc.formatDate('03/06/2024'), '632024');
  assert.equal(calc.formatDate('12/25/2024'), '25122024');
  assert.equal(calc.formatDate('nonsense'), null);
  assert.equal(calc.formatDateToYmd('3/6/2024'), '2024-03-06');
});

test('no load 45kw averages and power', () => {
  // [date, serial, amps, volts, hz, rpm]
  const rows = [[0, 'S1', 10, 400, 50, 2990], [0, 'S1', 12, 410, 50, 2980], [0, 'OTHER', 99, 99, 99, 99]];
  const r = calc.noLoad(rows, 'S1', '45kw');
  close(r.current, 11); close(r.voltage, 405); close(r.frequency, 50); close(r.speed, 2985);
  close(r.power, 405 * 11 * 0.89 * Math.sqrt(3));
  assert.equal(r.rows.length, 2);
  assert.equal(calc.noLoad(rows, 'NOPE', '45kw'), null);
});

test('lock rotor 5kw stores frequency in speed', () => {
  const rows = [[0, 'S1', 0, 0, 0, 20, 380, 49], [0, 'S1', 0, 0, 0, 22, 390, 51]];
  const r = calc.lockRotor(rows, 'S1', '5kw');
  close(r.current, 21); close(r.voltage, 385); close(r.speed, 50);
});

test('performance determination 45kw: buckets, extension and load table', () => {
  // 45kw columns: [0]date [1]hz [2]volt [3]serial [4]rpm [5]torque [6]amp [7]load [8..10] 5kw columns
  const rows = [
    [0, 50, 400, 'S1', 2990, 10, 5, '10%', 0, 0, 0],
    [0, 50, 400, 'S1', 2980, 11, 6, '10%', 0, 0, 0],
    [0, 50, 400, 'S1', 2900, 50, 20, '100%', 0, 0, 0],
    [0, 50, 400, 'S1', 2900, 50, 20, '100%', 0, 0, 0],      // duplicate → removed from mdb_data
    [0, 50, 0, 'S1', 2900, 50, 20, '50%', 0, 0, 0],         // zero voltage → dropped
    [0, 50, 400, 'S1', 2900, 50, 20, '55%', 0, 0, 0],       // unknown bucket → skipped
    [0, 50, 400, 'S2', 2900, 50, 20, '20%', 0, 0, 0],       // other motor
  ];
  const b = calc.alignLoadData(rows, 'S1', '45kw');
  assert.equal(b['10'].length, 2); assert.equal(b['100'].length, 2); assert.equal(b['50'].length, 0);
  assert.ok(calc.hasAnyBucket(b));

  const R = 0.3;
  const ext = calc.extendRows(b, R, '45kw');
  assert.equal(ext.length, 3);
  const first = ext[0];
  close(first[11], (10 * 2990) / 5252);
  close(first[12], 400 * 5 * Math.sqrt(3));
  close(first[13], ((10 * 2990) / (5 * 400 + 10 * 2990 + R * 25)) * 100);

  const t = calc.loadTable(b, R, '45kw');
  assert.equal(t.length, 10);
  const l10 = t[0];
  close(l10.current, 5.5); close(l10.speed, 2985);
  close(l10.slip, ((3000 - 2985) / 3000) * 100);
  assert.equal(l10.cos, 0.89);
  // 45kw rule: in the 100 % bucket both samples (20 A) are > prevCurrent (5.5) so both count
  close(t[9].current, 20);
  assert.deepEqual(t[4], { load: 50, current: 0, slip: 0, speed: 0, efficiency: 0, cos: 0 });

  const s = calc.chartSeries(ext, '45kw');
  assert.deepEqual(s.speed, [2900, 2980, 2990]);
  assert.deepEqual(s.amplitude, [20, 6, 5]);
});
