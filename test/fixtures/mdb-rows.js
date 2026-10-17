'use strict';
// Synthetic instrument rows standing in for .mdb tables (smoke test and demo seed). Column maps follow src/calc.js.
function makeRows(serial, testType = '45kw', kind = 'perf', k = 1) {
  const date = '2024-03-06', hz = 50;
  if (kind === 'perf') {
    const rows = [];
    for (let load = 10; load <= 100; load += 10) {
      for (let i = 0; i < 3; i++) {
        const rpm = 2995 - load * 0.9 * k - i, torque = (load * 2.9 + i * 0.1) * k, amp = (8 + load * 0.75 + i * 0.2) * k, volt = 400 - i;
        rows.push(testType === '45kw'
          ? [date, hz, volt, serial, rpm, torque, amp, `${load}%`, 0, 0, 0]
          : [date, 0, 0, serial, rpm, torque, 0, `${load}%`, amp, hz, volt]);
      }
    }
    return rows;
  }
  const samples = [[10.2 * k, 401, 2994], [10.4 * k, 399, 2993], [10.3 * k, 400, 2993]];
  return samples.map(([amp, volt, rpm]) => {
    if (kind === 'noload') return testType === '45kw' ? [date, serial, amp, volt, hz, rpm] : [date, serial, 0, 0, 0, rpm, amp, volt, hz];
    const la = amp * 6; // locked-rotor current
    return testType === '45kw' ? [date, serial, la, volt, hz, 0] : [date, serial, 0, 0, 0, la, volt, hz];
  }).concat([[date, 'OTHER-MOTOR', 1, 1, 1, 1, 1, 1, 1]]);
}

// `electron . --smoke` reader: table 632024 = 2024-03-06, file name tells the kind.
async function readMdbTable(filePath, table) {
  if (String(table) !== '632024') throw new Error('no table');
  return makeRows('SMOKE-1', '45kw', filePath.includes('perf') ? 'perf' : filePath.includes('lock') ? 'lock' : 'noload');
}
module.exports = readMdbTable;
module.exports.makeRows = makeRows;
