'use strict';
// Pure port of the formulas in motor_testing/views.py (branch window_graph_modification).
// Rows are arrays in .mdb column order; indices are the instrument export contract.

const POWER_FACTOR = 0.89;
const SQRT3 = Math.sqrt(3);
const LOADS = ['10', '20', '30', '40', '50', '60', '70', '80', '90', '100'];

const num = (v) => (v === null || v === undefined || v === '' ? 0 : Number(v));

// Date → .mdb table name: day+month+year without leading zeros (2024-03-06 → "632024").
function formatDate(dateStr) {
  const d = parseDate(dateStr);
  return d ? `${d.getDate()}${d.getMonth() + 1}${d.getFullYear()}` : null;
}

function formatDateToYmd(dateStr) {
  const d = parseDate(dateStr);
  if (!d) return null;
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// Accepts MM/DD/YYYY or YYYY-MM-DD, like the Django code.
function parseDate(s) {
  if (!s) return null;
  let m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s);
  if (m) return validDate(+m[3], +m[1], +m[2]);
  m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
  if (m) return validDate(+m[1], +m[2], +m[3]);
  return null;
}
function validDate(y, mo, d) {
  const dt = new Date(y, mo - 1, d);
  return dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d ? dt : null;
}

const filterBySerial = (rows, serial, idx) => rows.filter((r) => String(r[idx]) === String(serial));

// NoLoadFormSaveView: serial in column 1.
function noLoad(rows, serial, testType) {
  const data = filterBySerial(rows, serial, 1);
  if (!data.length) return null;
  const n = data.length;
  let rpm = 0, hz = 0, v = 0, a = 0;
  for (const r of data) {
    rpm += num(r[5]);
    if (testType === '45kw') { hz += num(r[4]); v += num(r[3]); a += num(r[2]); }
    else { hz += num(r[8]); v += num(r[7]); a += num(r[6]); }
  }
  const avgV = v / n, avgA = a / n;
  return {
    voltage: avgV, current: avgA, frequency: hz / n, speed: rpm / n,
    power: avgV * avgA * POWER_FACTOR * SQRT3, rows: data,
  };
}

// LockRotorFormSave: serial in column 1. `speed` holds the average frequency (Hz), as in the report.
function lockRotor(rows, serial, testType) {
  const data = filterBySerial(rows, serial, 1);
  if (!data.length) return null;
  const n = data.length;
  let hz = 0, v = 0, a = 0;
  for (const r of data) {
    if (testType === '45kw') { a += num(r[2]); v += num(r[3]); hz += num(r[4]); }
    else { a += num(r[5]); v += num(r[6]); hz += num(r[7]); }
  }
  const avgV = v / n, avgA = a / n;
  return { voltage: avgV, current: avgA, speed: hz / n, power: avgV * avgA * POWER_FACTOR * SQRT3, rows: data };
}

const perfCols = (testType) => (testType === '45kw'
  ? { voltage: 2, current: 6, hz: 1 }
  : { voltage: 10, current: 8, hz: 9 });

// PerformanceDeterminationFormSave.align_load_data: bucket rows by load % (column 7), serial in column 3.
function alignLoadData(rows, serial, testType) {
  const c = perfCols(testType);
  const buckets = Object.fromEntries(LOADS.map((k) => [k, []]));
  for (const r of rows) {
    if (String(r[3]) !== String(serial)) continue;
    const torque = num(r[5]), speed = num(r[4]), voltage = num(r[c.voltage]), current = num(r[c.current]);
    if (!(voltage && torque && speed && current)) continue;
    const key = String(r[7] ?? '').trim().replace(/^%+|%+$/g, '');
    // shortcut: Django raised KeyError (reported as "no record for date") for loads outside 10..100; we skip the row instead
    if (key && buckets[key]) buckets[key].push(r);
  }
  return buckets;
}

const hasAnyBucket = (buckets) => LOADS.some((k) => buckets[k].length > 0);

// perform_calculation_and_extend_determine_data_list + the set() de-duplication.
function extendRows(buckets, avgResistance, testType) {
  const c = perfCols(testType);
  const out = [];
  for (const k of LOADS) {
    for (const r of buckets[k]) {
      const speed = num(r[4]), current = num(r[c.current]), voltage = num(r[c.voltage]);
      if (!(current && speed && voltage)) continue;
      const torque = num(r[5]);
      const mech = torque * speed;
      const losses = avgResistance * current * current;
      const elec = current * voltage;
      const efficiency = (mech / (elec + mech + losses)) * 100;
      const horsepower = (torque * speed) / 5252;
      const wattsOut = voltage * current * SQRT3;
      out.push([...r, horsepower, wattsOut, efficiency]);
    }
  }
  const seen = new Set();
  return out.filter((r) => { const k = JSON.stringify(r); if (seen.has(k)) return false; seen.add(k); return true; });
}

// save_performance_test_parameters / create_performance_determination_obj: the 10-row load table.
function loadTable(buckets, avgResistance, testType) {
  const c = perfCols(testType);
  const table = [];
  let prevCurrent = 0;
  for (const k of LOADS) {
    const rows = buckets[k];
    const row = { load: Number(k), current: 0, slip: 0, speed: 0, efficiency: 0, cos: 0 };
    if (rows.length) {
      let current = 0, speed = 0, hz = 0, voltage = 0, torque = 0, currentCount = 0;
      for (const r of rows) {
        speed += num(r[4]);
        if (testType === '45kw') {
          if (num(r[c.current]) > prevCurrent) { current += num(r[c.current]); currentCount += 1; }
        } else { currentCount += 1; current += num(r[c.current]); }
        voltage += num(r[c.voltage]);
        hz += num(r[c.hz]);
        torque += num(r[5]);
      }
      const avgHz = hz / rows.length;
      if (current && voltage && speed && avgHz) {
        const avgCurrent = current / currentCount;
        const avgSpeed = speed / rows.length;
        const avgVoltage = voltage / rows.length;
        const avgTorque = torque / rows.length;
        const ns = (avgHz * 120) / 2;
        const mech = avgTorque * avgSpeed;
        const losses = avgResistance * avgCurrent * avgCurrent;
        const elec = avgCurrent * avgVoltage;
        row.current = avgCurrent;
        row.slip = ((ns - avgSpeed) / ns) * 100;
        row.speed = avgSpeed;
        row.efficiency = (mech / (elec + mech + losses)) * 100;
        row.cos = POWER_FACTOR;
      }
    }
    prevCurrent = row.current;
    table.push(row);
  }
  return table;
}

// ChartView: sort extended rows by speed and split into series.
function chartSeries(mdbData, testType) {
  const c = perfCols(testType);
  const rows = [...(mdbData || [])].sort((a, b) => num(a[4]) - num(b[4]));
  return {
    speed: rows.map((r) => num(r[4])),
    torque: rows.map((r) => num(r[5])),
    amplitude: rows.map((r) => num(r[c.current])),
    horsePower: rows.map((r) => num(r[11])),
    wattsOut: rows.map((r) => num(r[12])),
    efficiency: rows.map((r) => num(r[13])),
  };
}

module.exports = {
  POWER_FACTOR, LOADS, formatDate, formatDateToYmd, noLoad, lockRotor,
  alignLoadData, hasAnyBucket, extendRows, loadTable, chartSeries,
};
