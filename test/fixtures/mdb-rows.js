'use strict';
// Synthetic instrument rows for `electron . --smoke` (the real app reads .mdb files). Table name 632024 = 2024-03-06.
// Performance (45kw map): [date, hz, volt, serial, rpm, torque, amp, load, c8, c9, c10]
const perf = [];
for (let load = 10; load <= 100; load += 10) {
  for (let i = 0; i < 3; i++) {
    const rpm = 2995 - load * 0.9 - i, torque = load * 2.9 + i * 0.1, amp = 8 + load * 0.75 + i * 0.2;
    perf.push(['2024-03-06', 50, 400 - i, 'SMOKE-1', rpm, torque, amp, `${load}%`, 0, 0, 0]);
  }
}
// No load / lock rotor (45kw map): [date, serial, amp, volt, hz, rpm]
const noLoad = [['2024-03-06', 'SMOKE-1', 10.2, 401, 50, 2994], ['2024-03-06', 'SMOKE-1', 10.4, 399, 50, 2993], ['2024-03-06', 'OTHER', 1, 1, 1, 1]];

module.exports = async function readMdbTable(filePath, table) {
  if (String(table) !== '632024') throw new Error('no table');
  return filePath.includes('perf') ? perf : noLoad;
};
