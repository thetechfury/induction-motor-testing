'use strict';
// Faithful port of templates/induction_report.html. Markup and class names are unchanged so
// assets/report/induction_report.css applies as before. Values are formatted the way Django rendered them.

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// Django DecimalField(decimal_places=n) always rendered with n decimals; None rendered blank here (Django printed "None").
const dec = (v, n = 3) => (v === null || v === undefined || v === '' ? '' : Number(v).toFixed(n));
const txt = (v) => esc(v ?? '');
const mdy = (iso) => { const d = iso ? new Date(iso.replace(' ', 'T') + (iso.endsWith('Z') ? '' : 'Z')) : new Date(); const p = (n) => String(n).padStart(2, '0'); return `${p(d.getMonth() + 1)}/${p(d.getDate())}/${d.getFullYear()}`; };
const DIRECTION = { CLOCKWISE: 'Clockwise', ANTI_CLOCKWISE: 'Anti Clockwise' };
const TEST_ROWS = [
  ['electric_resistance_test', '1. Electric Resistance'], ['temperature_rise_test', '2. Temperature Rise - Nominal Condition'],
  ['performance_determination_test', '3. Performance Determination'], ['no_load_test', '4. No Load'],
  ['withstand_voltage_ac_test', '5. Withstand Voltage'], ['insulation_resistance_test', '6. Insulation Resistance'], ['lock_rotor_test', '7. Lock Rotor Test'],
];

function header(m, logo) {
  return `<header>
    <div class="main-heading">
      <img class="border-1" src="${logo}" alt=""/>
      <h1>Test Report <br/>Three Phase Induction Motor</h1>
      <h2 class="border-1"><b>Motor's Serial Number <br> ${txt(m.serial_number)}</b></h2>
    </div>
    <div class="second-heading border-1"><span>University of Engineering Technology</span><span>Motor Testing Lab</span></div>
    <div class="third-heading">University Rd. Kala Shah Kaku, Sheikhupura, Punjab</div>
  </header>`;
}

function performedTests(tests) {
  const by = Object.fromEntries(tests.map((t) => [t.test_type, t]));
  const x = (v) => (v ? '<td>X</td>' : '<td>-</td>');
  return TEST_ROWS.map(([key, label]) => {
    const t = by[key];
    return `<tr><td class="same-width-td">${label}</td>${t ? x(t.routine) + x(t.type) + x(t.special) : ''}</tr>`;
  }).join('');
}

function testSection(i, t, r, parameters) {
  const n = `3.${i}.`;
  switch (t.test_type) {
    case 'electric_resistance_test': {
      const e = r.electric_resistance_test;
      return `<h1 class="text"><span class="title">${n} Electric Resistance</span></h1>
      <ul class="section-ul test-margin-bottom">
        <li class="text-left" style="width:45%">Resistance (mOhms): ${dec(e.resistance_ohm_1)} / ${dec(e.resistance_ohm_2)} / ${dec(e.resistance_ohm_3)}</li>
        <li class="text-left" style="width:30%">Ambient Temperature (°C): ${dec(e.ambient_temperature_C)}</li>
        <li class="text-left" style="margin-left:20px;width:20%;">Unbalance (%): ${dec(e.unbalance_percentage)}</li>
      </ul>`;
    }
    case 'temperature_rise_test': {
      const e = r.temperature_rise_test;
      // Label/field crossing (Frequency shows `winding`, Winding shows `frequency`) kept from the original template.
      return `<h1 class="text"><span class="title">${n} Temperature Rise - Nominal Condition - Direct</span></h1>
      <ul class="section-ul-3 test-margin-bottom">
        <li>Voltage (V): ${dec(e.voltage)}</li>
        <li style="padding-left:17px;">Frequency (Hz): ${dec(e.winding)}</li>
        <li style="margin-left:-10px;">Winding(Resistance Method)(C): ${dec(e.frequency)}</li>
        <li>DE Bearing (C): ${dec(e.de_bearing)}</li>
        <li style="padding-left:17px;">NDE Bearing (C): ${dec(e.nde_bearing)}</li>
      </ul>`;
    }
    case 'performance_determination_test': {
      const e = r.performance_determination_test;
      return `<h1 class="text"><span class="title">${n} Performance Determination</span></h1>
      <ul class="section-ul test-margin-bottom">
        <li class="text-left">Voltage (V): ${dec(e.voltage)}</li>
        <li class="text-left">Frequency (Hz): ${dec(e.frequency)}</li>
        <li class="text-left">Nominal T. (N.m): ${dec(e.nominal_t)}</li>
      </ul>
      <table class="table-border">
        <tr><th>Load (%)</th><th>Current (A)</th><th>Slip(%)</th><th>Speed (rpm)</th><th>Efficiency (%)</th><th>Cos Ø</th></tr>
        ${parameters.filter((p) => p.load).map((p) => `<tr><td>${p.load}</td><td>${dec(p.current)}</td><td>${dec(p.slip)}</td><td>${dec(p.speed)}</td><td>${dec(p.efficiency)}</td><td>${dec(p.cos)}</td></tr>`).join('')}
      </table>`;
    }
    case 'no_load_test': {
      const e = r.no_load_test;
      return `<h1 class="text"><span class="title">${n} No Load</span></h1>
      <ul class="section-ul-3 test-margin-bottom">
        <li>Voltage (V): ${dec(e.voltage)}</li>
        <li>Current (A): ${dec(e.current)}</li>
        <li style="margin-left:-40px;">Power (W): ${dec(e.power)}</li>
        <li>Frequency (Hz): ${dec(e.frequency)}</li>
        <li>Speed (rpm): ${dec(e.speed)}</li>
        <li style="margin-left:-40px;width: 40%;">Direction of Rotation: ${DIRECTION[e.direction_of_rotation] || ''}</li>
      </ul>`;
    }
    case 'withstand_voltage_ac_test': {
      const e = r.withstand_voltage_ac_test;
      return `<h1 class="text"><span class="title">${n} Withstand Voltage AC</span></h1>
      <table class="table-border test-margin-bottom">
        <tr><th>Description</th><th>Voltage (kV)</th><th>Time (s)</th></tr>
        <tr><td>${txt(e.description)} </td><td>${dec(e.voltage_kv)}</td><td>${txt(e.time_in_seconds)}</td></tr>
      </table>`;
    }
    case 'insulation_resistance_test': {
      const e = r.insulation_resistance_test;
      return `<h1 class="text"><span class="title">${n} Insulation Resistance</span></h1>
      <table class="table-border test-margin-bottom">
        <tr><th>Description</th><th>Voltage (V)</th><th>Insulation Res. (Mohms)</th><th>Time (s)</th></tr>
        <tr><td> ${txt(e.description)} </td><td>${dec(e.voltage)}</td><td>${dec(e.insulation_resistance)}</td><td>${txt(e.time_in_seconds)}</td></tr>
      </table>
      <ul class="section-ul-4 test-margin-bottom">
        <li>Ambient Temperature (°C): ${dec(e.ambient_temperature_C)}</li>
        <li>Humidity (%): ${dec(e.humidity_percentage)}</li>
      </ul>`;
    }
    default: return '';
  }
}

function remarks(m, r) {
  const items = [
    ['Final Remarks', m.remarks], ['Electric Resistance Test Remarks', r.electric_resistance_test.remarks],
    ['Temperature Rise Test Remarks', r.temperature_rise_test.remarks], ['Performance Determination Test Remarks', r.performance_determination_test.remarks],
    ['No Load Test Remarks', r.no_load_test.remarks], ['With Stand Voltage AC Test Remarks', r.withstand_voltage_ac_test.remarks],
    ['Insulation Resistance Test Remarks', r.insulation_resistance_test.remarks], ['Lock Rotor  Test Remarks', r.lock_rotor_test.remarks],
  ];
  return items.filter(([, v]) => v).map(([k, v]) => `<p><b>${k}</b>: ${txt(v)}</p>`).join('\n');
}

/**
 * @param data result of services['report.data']
 * @param assets { css: string, logoDataUri: string, print?: boolean } — print adds the Chromium page rules
 */
function renderReport({ motor: m, tests, completed, results: r, parameters, hasLockRotor }, { css, logoDataUri, print = false }) {
  const lr = r.lock_rotor_test;
  const issued = mdy(m.updated_on);
  const printCss = print ? '@page{size:A4;margin:10mm}.page-main-1{page-break-after:always}' : '';
  return `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>${txt(m.serial_number)} motor report</title><style>${css}${printCss}</style></head>
<body>
<div class="page-main-1">
  <div class="border-1 page-1">
    ${header(m, logoDataUri)}
    <section class="main-section">
      <div class="section-1">
        <h1 class="text"><span class="title">Customer:</span> ${txt(m.customer_name)}</h1>
        <h1 class="text"><span class="title">Sales Order:</span> ${txt(m.sales_order_number)}</h1>
      </div>
      <h1 class="main-title">1. Motor Identification</h1>
      <div class="section-2">
        <table>
          <tr><td>TAG: ${txt(m.tag)}</td><td>Motor Power(KW): ${txt(m.test_type)}</td></tr>
          <tr><td>Material: ${txt(m.material)}</td><td>Enclosure: ${txt(m.enclosure)}</td><td>Insulation Class: ${txt(m.insulation_class)}</td></tr>
          <tr><td>Frame: ${txt(m.frame)}</td><td>Altitude (m): ${txt(m.altitude_M)}</td><td>Temperature Rise (C): ${dec(m.temperature_rise_K)}</td></tr>
          <tr><td>Mounting: ${txt(m.mounting)}</td><td>Duty Cycle: ${txt(m.duty_cycle)}</td><td>Ambient Temperature (°C): ${dec(m.ambient_temperature_C)}</td></tr>
          <tr><td>Drawing: ${txt(m.drawing)}</td><td>Design: ${txt(m.design)}</td><td>Service Factor: ${dec(m.service_factor)}</td></tr>
        </table>
        <table class="table-border">
          <tr><th>Voltage (V)</th><th>Current (A)</th><th>Power (kW)</th><th>Freq. (Hz)</th><th>Speed (rpm)</th><th>P.F.</th><th>Eff. (%)</th></tr>
          <tr><td>${txt(m.voltage)}</td><td>${txt(m.current)}</td><td>${txt(m.power)}</td><td>${txt(m.frequency)}</td><td>${txt(m.speed)}</td><td>${dec(m.p_f, 2)}</td><td>${dec(m.efficiency, 2)}</td></tr>
        </table>
      </div>
      <h1 class="main-title">2. Performed Tests</h1>
      <section class="section-3">
        <table class="table-border">
          <tr><th class="same-width-td"></th><th>Routine</th><th>Type</th><th>Special</th></tr>
          ${performedTests(tests)}
        </table>
      </section>
      <h1 class="main-title">3. Tests</h1>
      <section class="section-4">
        ${completed.map((t, i) => testSection(i + 1, t, r, parameters)).join('\n')}
      </section>
    </section>
    <footer class="footer-1" style="margin-top:50px;">
      <hr/>
      <ul class="footer-ul">
        <li>Confidential report. Reproduction of this document shall not be partial and depends on the written approval of the laboratory</li>
        <li>The results presented in this document refer exclusively to the electric motor subjected to the specified tests and do not extend to any batch</li>
        <li> WEG will keep the original document archived for at least five years.</li>
      </ul>
      <div style="padding:10px;">Report issued on ${issued}</div>
    </footer>
  </div>
  <p class="page-number first-page">Page 1 of 2</p>
</div>
<div class="page-main-2">
  <div class="border-1 page-2">
    ${header(m, logoDataUri)}
    <section class="main-section">
      ${hasLockRotor ? `<h1 class="main-title">4. Lock Rotor Test</h1>
      <section class="section-5">
        <table class="table-border test-margin-bottom">
          <tr><th>Tested Perimeters for 5 seconds</th><th>Value</th></tr>
          <tr><td>Voltage (V)</td><td> ${dec(lr.voltage)}</td></tr>
          <tr><td>Frequency (Hz)</td><td>${dec(lr.speed)}</td></tr>
          <tr><td>Current (A)</td><td>${dec(lr.current)}</td></tr>
          <tr><td>Power (KW)</td><td>${Math.round((lr.power || 0) / 1000)} </td></tr>
          <tr><td>Vibration (mm/s)</td><td>${dec(lr.vibration)}</td></tr>
          <tr><td>Noise (db.)</td><td>${dec(lr.noise)}</td></tr>
          <tr><td>Temperature (°C)</td><td>${dec(lr.temperature)}</td></tr>
        </table>
      </section>` : ''}
      <h1 class="main-title">${hasLockRotor ? 5 : 4}. Result</h1>
      <section class="section-4">
        ${remarks(m, r)}
      </section>
    </section>
    <section class="section-4"></section>
    <footer class="footer-2">
      <table class="table-border">
        <tr><th style="padding:5px;">UET TEST REOPRT</th><th style="padding:5px;">Customer</th></tr>
        <tr style="padding:20px;">
          <td style="padding:10px;">
            <table class="concern-persons">
              <tr class="concern-title"><td>Director Cerad</td><td>Lab Instructor</td></tr>
              <tr class="concern-name"><td style="font-weight: 300;">${txt(m.director_cerad)}</td><td style="font-weight: 300;">${txt(m.lab_instructor)}</td></tr>
            </table>
          </td>
          <td style="padding:5px">Inspector</td>
        </tr>
        <tr><td colspan="2" style="padding:10px;">Report issued on ${issued}</td></tr>
      </table>
    </footer>
  </div>
  <p class="page-number">Page 2 of 2</p>
</div>
</body></html>`;
}

module.exports = { renderReport };
