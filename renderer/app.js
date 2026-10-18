'use strict';
/* Single-page UI. All data access goes through window.bridge.call(name, payload) → main process services. */
const api = (name, payload) => window.bridge.call(name, payload);
const root = document.getElementById('app');

const TESTS = {
  electric_resistance_test: { label: 'Electric Resistance', kind: 'manual', num: 3.1,
    fields: [['resistance_ohm_1', 'Resistance 1 (mΩ)'], ['resistance_ohm_2', 'Resistance 2 (mΩ)'], ['resistance_ohm_3', 'Resistance 3 (mΩ)'], ['ambient_temperature_C', 'Ambient temperature (°C)']] },
  temperature_rise_test: { label: 'Temperature Rise', kind: 'manual',
    fields: [['voltage', 'Voltage (V)'], ['winding', 'Winding, resistance method (°C)'], ['frequency', 'Frequency (Hz)'], ['de_bearing', 'DE bearing (°C)'], ['nde_bearing', 'NDE bearing (°C)']] },
  performance_determination_test: { label: 'Performance Determination', kind: 'import',
    fields: [['voltage', 'Voltage (V)'], ['frequency', 'Frequency (Hz)'], ['nominal_t', 'Nominal torque (N.m)']] },
  no_load_test: { label: 'No Load', kind: 'import', fields: [],
    results: [['voltage', 'Voltage (V)'], ['current', 'Current (A)'], ['power', 'Power (W)'], ['frequency', 'Frequency (Hz)'], ['speed', 'Speed (rpm)']] },
  withstand_voltage_ac_test: { label: 'Withstand Voltage AC', kind: 'manual',
    fields: [['description', 'Description', 'text'], ['voltage_kv', 'Voltage (kV)'], ['time_in_seconds', 'Time (s)']] },
  insulation_resistance_test: { label: 'Insulation Resistance', kind: 'manual',
    fields: [['description', 'Description', 'text'], ['voltage', 'Voltage (V)'], ['insulation_resistance', 'Insulation resistance (MΩ)'], ['time_in_seconds', 'Time (s)'], ['ambient_temperature_C', 'Ambient temperature (°C)'], ['humidity_percentage', 'Humidity (%)']] },
  lock_rotor_test: { label: 'Lock Rotor', kind: 'import',
    fields: [['vibration', 'Vibration (mm/s)'], ['noise', 'Noise (dB)'], ['temperature', 'Temperature (°C)']],
    results: [['voltage', 'Voltage (V)'], ['speed', 'Frequency (Hz)'], ['current', 'Current (A)'], ['power', 'Power (W)']] },
};
const ORDER = Object.keys(TESTS);
const MOTOR_SECTIONS = [
  ['Order', [['serial_number', 'Serial number *', 'text'], ['customer_name', 'Customer *', 'text'], ['sales_order_number', 'Sales order *', 'text'],
    ['test_type', 'Motor type *', 'select', [['45kw', '45 KW'], ['5kw', 'Up to 5 KW']]], ['power', 'Rated power (kW) *'], ['director_cerad', 'Director CERAD', 'text'], ['lab_instructor', 'Lab instructor', 'text']]],
  ['Identification', [['tag', 'TAG', 'text'], ['material', 'Material', 'text'], ['frame', 'Frame', 'text'], ['mounting', 'Mounting', 'text'], ['drawing', 'Drawing', 'text'], ['enclosure', 'Enclosure', 'text'],
    ['duty_cycle', 'Duty cycle', 'text'], ['design', 'Design', 'text'], ['insulation_class', 'Insulation class', 'text'], ['altitude_M', 'Altitude (m)'], ['temperature_rise_K', 'Temperature rise (K)'], ['ambient_temperature_C', 'Ambient temperature (°C)'], ['service_factor', 'Service factor']]],
  ['Nameplate', [['voltage', 'Voltage (V)'], ['current', 'Current (A)'], ['frequency', 'Frequency (Hz)'], ['speed', 'Speed (rpm)'], ['p_f', 'Power factor'], ['efficiency', 'Efficiency (%)']]],
];

const state = { user: null, screen: 'login', search: '', motors: [], motorId: null, data: null, test: null, preview: null, mdbPaths: {}, armed: null,
  reportTab: 'report', reportHtml: '', draft: null, settings: {}, users: [], info: {}, toast: null, busy: false };
let chartInstance = null;

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (v, n = 3) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(n));
const val = (v) => (v === null || v === undefined ? '' : v);
const when = (iso) => (iso ? new Date(iso.replace(' ', 'T') + 'Z').toLocaleDateString() : '');
const statusChip = (s) => (s === 'COMPLETED' ? '<span class="chip ok"><i></i>Completed</span>' : s === 'PENDING' ? '<span class="chip pend"><i></i>Pending</span>' : '<span class="chip"><i></i>Not selected</span>');

function toast(msg, kind = '') {
  state.toast = { msg, kind };
  render();
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { state.toast = null; render(); }, 4000);
}
async function guard(fn) {
  try { return await fn(); } catch (e) { toast(e.message, 'bad'); return undefined; }
}

/* ---------- views ---------- */
const field = ([name, label, type = 'number', options], value, extra = '') => `
  <div class="field"><label for="f_${name}">${label}</label>
  ${type === 'select' ? `<select class="input" id="f_${name}" name="${name}">${options.map(([v, l]) => `<option value="${v}" ${String(value) === v ? 'selected' : ''}>${l}</option>`).join('')}</select>`
    : type === 'textarea' ? `<textarea class="input" id="f_${name}" name="${name}" maxlength="250">${esc(value)}</textarea>`
    : `<input class="input ${type === 'number' ? 'num' : ''}" id="f_${name}" name="${name}" type="${type}" ${type === 'number' ? 'step="any" min="0"' : ''} value="${esc(value)}" ${extra}>`}
  </div>`;

function sidebar() {
  const nav = (id, label, icon) => `<button class="navbtn ${state.screen === id || (id === 'motors' && ['motor', 'workspace', 'report'].includes(state.screen)) ? 'on' : ''}" data-action="go" data-screen="${id}">${icon}<span>${label}</span></button>`;
  return `<aside class="sidebar">
    <div class="brand"><span class="mark">${ICON.bolt}</span><div><b>Motor Lab</b><small>UET · Kala Shah Kaku</small></div></div>
    <nav>${nav('motors', 'Motors', ICON.motors)}${nav('settings', 'Settings', ICON.settings)}</nav>
    <div class="sidefoot"><div class="avatar">${esc(state.user.username.slice(0, 2).toUpperCase())}</div><div class="who"><b>${esc(state.user.username)}</b><small>signed in</small></div><button class="iconbtn" data-action="logout" title="Log out" aria-label="Log out">${ICON.logout}</button></div>
  </aside>`;
}
const ICON = {
  bolt: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/></svg>',
  motors: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="13" height="10" rx="2"/><path d="M16 10h3l2 2v3h-5M6 17v2M13 17v2M3 11H1M3 13H1"/></svg>',
  settings: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
  logout: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></svg>',
  check: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
  plus: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  pdf: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg>',
  back: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>',
};
const curveSvg = `<svg class="curve" viewBox="0 0 400 220" aria-hidden="true"><defs><linearGradient id="g1" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#8fb8ff" stop-opacity=".45"/><stop offset="1" stop-color="#8fb8ff" stop-opacity="0"/></linearGradient></defs>
  <g stroke="rgba(255,255,255,.08)" stroke-width="1">${[40, 80, 120, 160, 200].map((y) => `<line x1="0" x2="400" y1="${y}" y2="${y}"/>`).join('')}${[80, 160, 240, 320].map((x) => `<line y1="0" y2="220" x1="${x}" x2="${x}"/>`).join('')}</g>
  <path d="M0 200 C 90 190, 150 150, 210 120 S 330 60, 400 30 L 400 220 L 0 220 Z" fill="url(#g1)"/>
  <path d="M0 200 C 90 190, 150 150, 210 120 S 330 60, 400 30" fill="none" stroke="#8fb8ff" stroke-width="3" stroke-linecap="round"/>
  <path d="M0 40 C 80 45, 160 70, 230 120 S 350 205, 400 210" fill="none" stroke="#f0b35a" stroke-width="3" stroke-linecap="round"/>
  <path d="M0 150 C 100 60, 200 50, 400 55" fill="none" stroke="#5fcf93" stroke-width="3" stroke-linecap="round" stroke-dasharray="6 7"/></svg>`;

const views = {
  login: () => `<div class="login">
    <section class="login-hero">
      <div class="brand light"><span class="mark">${ICON.bolt}</span><div><b>Motor Lab</b><small>University of Engineering &amp; Technology</small></div></div>
      <div class="hero-copy"><h1>Three-phase induction motor test reports</h1><p>Record the seven standard tests, import instrument data, and print the laboratory report. Everything runs on this machine, no internet needed.</p></div>
      ${curveSvg}
      <p class="hero-foot">Motor Testing Lab · University Rd. Kala Shah Kaku, Sheikhupura</p>
    </section>
    <section class="login-pane"><form class="login-card" data-action="login">
      <div><p class="eyebrow">Welcome back</p><h2>Sign in to continue</h2></div>
      <div class="field"><label for="f_username">Username</label><input class="input" id="f_username" name="username" autocomplete="username" autofocus required></div>
      <div class="field"><label for="f_password">Password</label><input class="input" id="f_password" name="password" type="password" autocomplete="current-password" required></div>
      <button class="btn primary lg" type="submit">Sign in</button>
      <p class="muted small">Users and passwords are managed under Settings.</p>
    </form></section></div>`,

  motors: () => {
    const ms = state.motors; const ready = ms.filter((m) => m.report_link).length; const prog = ms.filter((m) => m.completed_tests && m.completed_tests < m.total_tests).length;
    return `<div class="page-head"><div><p class="eyebrow">Overview</p><h1>Motors</h1></div>
      <div class="actions"><input class="input search" id="search" type="search" placeholder="Search serial number…" value="${esc(state.search)}" data-action="search">
      <button class="btn primary" data-action="new-motor">${ICON.plus}New motor</button></div></div>
    <div class="tiles">
      <div class="tile"><small>Active motors</small><b>${ms.length}</b></div>
      <div class="tile"><small>Reports exported</small><b>${ready}</b><span class="spark ok" style="--p:${ms.length ? (100 * ready) / ms.length : 0}%"></span></div>
      <div class="tile"><small>Tests in progress</small><b>${prog}</b><span class="spark warn" style="--p:${ms.length ? (100 * prog) / ms.length : 0}%"></span></div>
      <div class="tile"><small>Not started</small><b>${ms.filter((m) => !m.completed_tests).length}</b></div>
    </div>
    <div class="card flat">${ms.length ? `<table class="table"><thead><tr><th>Serial</th><th>Customer</th><th>Sales order</th><th>Type</th><th>Tests</th><th>Updated</th><th></th></tr></thead><tbody>
      ${ms.map((m) => `<tr class="click" data-action="open" data-id="${m.id}">
        <td><div class="serial"><span class="dot ${m.completed_tests === m.total_tests ? 'ok' : m.completed_tests ? 'warn' : ''}"></span><b>${esc(m.serial_number)}</b></div></td><td>${esc(m.customer_name)}</td><td class="muted">${esc(m.sales_order_number)}</td><td><span class="tag">${m.test_type === '45kw' ? '45 kW' : '≤ 5 kW'}</span></td>
        <td><div class="prog"><div class="bar"><b style="width:${m.total_tests ? (100 * m.completed_tests) / m.total_tests : 0}%"></b></div><span>${m.completed_tests}/${m.total_tests}</span>${m.report_link ? `<span class="chip ok">${ICON.pdf}PDF</span>` : ''}</div></td>
        <td class="muted">${when(m.updated_on)}</td>
        <td><div class="actions end"><button class="btn sm ghost" data-action="report" data-id="${m.id}">Report</button>
          <button class="btn sm ghost danger ${state.armed === m.id ? 'armed' : ''}" data-action="delete" data-id="${m.id}">${state.armed === m.id ? 'Confirm delete' : 'Delete'}</button></div></td></tr>`).join('')}
      </tbody></table>` : `<div class="empty"><div class="empty-art">${ICON.motors}</div><h2>No motors yet</h2><p>Create the first one with “New motor”.</p></div>`}</div>`;
  },

  motor: () => {
    const m = state.data?.motor || { test_type: '45kw' };
    const tests = Object.fromEntries((state.data?.tests || []).map((t) => [t.test_type, t]));
    return `<form data-action="save-motor" class="content" style="padding:0">
      <div class="page-head"><div><p class="eyebrow">${state.motorId ? esc(state.data?.motor.serial_number) : 'Registration'}</p><h1>${state.motorId ? 'Edit motor' : 'New motor'}</h1><p class="sub">Fields marked * are required. At least one test must be selected.</p></div>
        <div class="actions"><button class="btn" type="button" data-action="go" data-screen="${state.motorId ? 'workspace' : 'motors'}">Cancel</button><button class="btn primary" type="submit">${state.motorId ? 'Save changes' : 'Create motor and open tests'}</button></div></div>
      ${MOTOR_SECTIONS.map(([title, fields]) => `<section class="card"><h3>${title}</h3><div class="form-grid">${fields.map((f) => field(f, val(m[f[0]]))).join('')}</div></section>`).join('')}
      <section class="card"><div class="card-head"><h3>Tests to perform</h3><span class="muted">Tick Routine, Type or Special for each test that applies</span></div>
        <table class="table"><thead><tr><th>Test</th><th>Source</th><th>Routine</th><th>Type</th><th>Special</th>${state.motorId ? '<th>Status</th>' : ''}</tr></thead><tbody>
        ${ORDER.map((k, i) => `<tr><td>${i + 1}. ${TESTS[k].label}</td><td><span class="chip">${TESTS[k].kind === 'import' ? '.mdb import' : 'manual'}</span></td>
          ${['routine', 'type', 'special'].map((c) => `<td><input type="checkbox" name="${k}:${c}" ${tests[k]?.[c] ? 'checked' : ''} aria-label="${TESTS[k].label} ${c}"></td>`).join('')}
          ${state.motorId ? `<td>${statusChip(tests[k]?.status)}</td>` : ''}</tr>`).join('')}</tbody></table></section></form>`;
  },

  workspace: () => {
    const d = state.data; if (!d) return '';
    const m = d.motor;
    const selected = ORDER.filter((k) => d.statuses[k]);
    const unselected = ORDER.filter((k) => !d.statuses[k]);
    return `<div class="page-head"><div><p class="eyebrow">${esc(m.customer_name)} · ${esc(m.sales_order_number)}</p><h1>${esc(m.serial_number)}</h1><p class="sub">${m.test_type === '45kw' ? '45 kW' : 'Up to 5 kW'} column map · ${Object.values(d.statuses).filter((x) => x === 'COMPLETED').length} of ${Object.keys(d.statuses).length} tests completed</p></div>
      <div class="actions"><button class="btn ghost" data-action="go" data-screen="motors">${ICON.back}Motors</button><button class="btn" data-action="edit-motor">Edit motor</button><button class="btn primary" data-action="report" data-id="${m.id}">Report &amp; curve</button></div></div>
    ${d.allCompleted ? `<div class="note ok">${ICON.check} All selected tests are completed. The report is ready to export.</div>` : ''}
    <div class="workspace"><aside class="side">
      ${selected.map((k, i) => `<button class="item ${state.test === k ? 'on' : ''} ${d.statuses[k] === 'COMPLETED' ? 'done' : ''}" data-action="pick-test" data-test="${k}"><span class="step">${d.statuses[k] === 'COMPLETED' ? ICON.check : i + 1}</span><span class="grow">${TESTS[k].label}<small>${TESTS[k].kind === 'import' ? '.mdb import' : 'manual entry'}</small></span></button>`).join('')}
      ${unselected.length ? `<p class="muted" style="margin-top:8px;font-size:12px">Not selected: ${unselected.map((k) => TESTS[k].label).join(', ')}</p>` : ''}
    </aside><div>${state.test ? testPanel(state.test) : '<div class="card empty">Pick a test on the left.</div>'}</div></div>`;
  },

  report: () => {
    const d = state.data; if (!d) return '';
    const m = d.motor;
    const perfDone = d.statuses.performance_determination_test === 'COMPLETED';
    return `<div class="page-head"><div><p class="eyebrow">${esc(m.customer_name)} · ${esc(m.serial_number)}</p><h1>Report studio</h1><p class="sub">Only completed tests appear in the report</p></div>
      <div class="actions"><button class="btn ghost" data-action="open" data-id="${m.id}">${ICON.back}Tests</button>
        ${state.reportTab === 'report' ? `<button class="btn primary" data-action="export-pdf" ${state.busy ? 'disabled' : ''}>${ICON.pdf}${state.busy ? 'Exporting…' : 'Export PDF'}</button>` : `<button class="btn primary" data-action="save-png" ${perfDone ? '' : 'disabled'}>Save chart as PNG</button>`}</div></div>
    <div class="tabs"><button class="tab ${state.reportTab === 'report' ? 'on' : ''}" data-action="tab" data-tab="report">Report</button><button class="tab ${state.reportTab === 'chart' ? 'on' : ''}" data-action="tab" data-tab="chart">Performance curve</button></div>
    ${state.reportTab === 'report' ? `<div class="studio"><div style="display:grid;gap:16px">
        <form class="card" data-action="save-remarks"><h3>Final remarks</h3><textarea class="input" name="remarks" maxlength="500" rows="5">${esc(m.remarks)}</textarea><div class="actions"><button class="btn" type="submit">Save remarks</button></div></form>
        <div class="card"><h3>Signatories</h3><div class="kv"><div><small>Director CERAD</small><b style="font-family:inherit">${esc(m.director_cerad) || '—'}</b></div><div><small>Lab instructor</small><b style="font-family:inherit">${esc(m.lab_instructor) || '—'}</b></div></div><p class="muted" style="font-size:13px">Change these under “Edit motor”.</p></div>
        <div class="card"><h3>PDF</h3>${m.report_link ? `<div class="pathrow"><code title="${esc(m.report_link)}">${esc(m.report_link)}</code></div><div class="actions"><button class="btn sm" data-action="open-file" data-path="${esc(m.report_link)}">Open PDF</button><button class="btn sm" data-action="show-file" data-path="${esc(m.report_link)}">Show in folder</button></div>` : '<p class="muted">No PDF exported yet. “Export PDF” saves it to the reports folder set in Settings.</p>'}</div>
      </div><div class="preview"><iframe title="Report preview" sandbox="" srcdoc="${esc(state.reportHtml)}"></iframe></div></div>`
      : `<div class="chart-wrap">${perfDone ? '<canvas id="chart" height="620"></canvas>' : '<div class="empty">The curve needs a completed Performance Determination test.</div>'}</div>`}`;
  },

  settings: () => {
    const s = state.settings; const paths = JSON.parse(s.mdb_paths || '{}');
    return `<div class="page-head"><div><p class="eyebrow">Workstation</p><h1>Settings</h1></div></div>
    <div class="card"><h3>PDF reports</h3>
      <div class="field"><label>Reports folder</label><div class="pathrow"><code>${esc(s.reports_dir || state.info.reportsDir)}</code><button class="btn sm" data-action="pick-folder">Change…</button>${s.reports_dir ? '<button class="btn sm" data-action="set" data-key="reports_dir" data-value="">Reset</button>' : ''}</div></div>
      <form class="field" data-action="save-scale" style="max-width:320px"><label for="f_scale">Print scale</label><div class="pathrow"><input class="input num" id="f_scale" name="pdf_scale" type="number" step="0.01" min="0.5" max="1" value="${esc(s.pdf_scale || '0.74')}"><button class="btn sm" type="submit">Save</button></div><span class="hint">0.74 fits the report on A4 like the old wkhtmltopdf output. Lower it slightly if page 1 spills onto a third page.</span></form></div>
    <div class="card"><h3>Remembered instrument files</h3>${ORDER.filter((k) => TESTS[k].kind === 'import').map((k) => `<div class="field"><label>${TESTS[k].label}</label><div class="pathrow"><code>${esc(paths[k] || 'not chosen yet')}</code>${paths[k] ? `<button class="btn sm" data-action="forget-mdb" data-test="${k}">Forget</button>` : ''}</div></div>`).join('')}</div>
    <div class="card"><div class="card-head"><h3>Users</h3></div>
      <table class="table"><tbody>${state.users.map((u) => `<tr><td>${esc(u.username)}</td><td class="muted">since ${when(u.created_on)}</td><td style="text-align:right"><button class="btn sm danger ${state.armed === 'u' + u.id ? 'armed' : ''}" data-action="remove-user" data-id="${u.id}" ${u.id === state.user.id ? 'disabled' : ''}>${state.armed === 'u' + u.id ? 'Confirm' : 'Remove'}</button></td></tr>`).join('')}</tbody></table>
      <form class="form-grid" data-action="add-user"><div class="field"><label for="f_nu">New username</label><input class="input" id="f_nu" name="username" required></div><div class="field"><label for="f_np">Password</label><input class="input" id="f_np" name="password" type="password" minlength="4" required></div><div class="field"><label>&nbsp;</label><button class="btn" type="submit">Add user</button></div></form></div>
    <div class="card"><h3>Change my password</h3><form class="form-grid" data-action="change-password">
      <div class="field"><label for="f_cp">Current password</label><input class="input" id="f_cp" name="current" type="password" required></div>
      <div class="field"><label for="f_npw">New password</label><input class="input" id="f_npw" name="next" type="password" minlength="4" required></div>
      <div class="field"><label>&nbsp;</label><button class="btn" type="submit">Change password</button></div></form></div>
    <div class="card"><h3>About</h3><p class="muted" style="font-size:13px">Version ${esc(state.info.version)} · Database <span class="mono">${esc(state.info.dbPath)}</span> · Works fully offline.</p></div>`;
  },
};

function testPanel(k) {
  const t = TESTS[k]; const d = state.data; const r = d.results[k] || {}; const done = d.statuses[k] === 'COMPLETED';
  const head = `<div class="card-head"><div><h2>${t.label}</h2><p class="muted" style="font-size:13px">${t.kind === 'import' ? 'Values are read from the instrument .mdb file for the chosen date and this motor\'s serial number.' : 'Enter the measured values. Empty numbers are stored as 0.'}</p></div>${statusChip(d.statuses[k])}</div>`;
  const remarks = field(['remarks', 'Remarks', 'textarea'], r.remarks);
  if (t.kind === 'manual') {
    const extra = k === 'electric_resistance_test' ? `<div class="field"><label>Unbalance (%)</label><input class="input num" id="unbalance" readonly value="${fmt(r.unbalance_percentage)}"><span class="hint">|R1−R2| + |R1−R3| + |R2−R3|, computed on save</span></div>` : '';
    return `<form class="card" data-action="save-manual">${head}<div class="form-grid">${t.fields.map((f) => field(f, val(r[f[0]]))).join('')}${extra}<div class="wide">${remarks}</div></div>
      <div class="actions"><button class="btn primary" type="submit">${done ? 'Save changes' : 'Save and mark completed'}</button></div></form>`;
  }
  const mdbPath = state.mdbPaths[k] || '';
  const dv = state.draft?.test === k ? state.draft : {}; // values typed before "Preview import"
  const v = (f) => val(dv[f] !== undefined ? dv[f] : r[f]);
  const date = dv.dateStr !== undefined ? dv.dateStr : (k === 'performance_determination_test' ? r.report_date : r.reported_date);
  const p = state.preview?.test === k ? state.preview : null;
  const resultsBlock = (vals, title) => vals ? `<div><h3>${title}</h3><div class="kv" style="margin-top:8px">${t.results.map(([f, l]) => `<div><small>${l}</small><b>${fmt(vals[f])}</b></div>`).join('')}</div></div>` : '';
  const tableBlock = (rows, title) => rows?.length ? `<div><h3>${title}</h3><table class="table" style="margin-top:8px"><thead><tr><th class="num">Load %</th><th class="num">Current (A)</th><th class="num">Slip %</th><th class="num">Speed (rpm)</th><th class="num">Efficiency %</th><th class="num">Cos φ</th></tr></thead><tbody>
      ${rows.map((x) => `<tr><td class="num">${x.load}</td><td class="num">${fmt(x.current)}</td><td class="num">${fmt(x.slip)}</td><td class="num">${fmt(x.speed)}</td><td class="num">${fmt(x.efficiency)}</td><td class="num">${fmt(x.cos)}</td></tr>`).join('')}</tbody></table></div>` : '';
  return `<form class="card" data-action="import" data-test="${k}">${head}
    <div class="form-grid">
      <div class="field"><label for="f_date">Test date</label><input class="input" id="f_date" name="dateStr" type="date" value="${esc(date || '')}" required><span class="hint">Table name in the .mdb: day, month and year without leading zeros</span></div>
      <div class="field wide"><label>Instrument file (.mdb)</label><div class="pathrow"><code>${esc(mdbPath || 'No file chosen')}</code><button class="btn sm" type="button" data-action="pick-mdb" data-test="${k}">Choose file…</button></div></div>
      ${k === 'no_load_test' ? field(['direction_of_rotation', 'Direction of rotation', 'select', [['CLOCKWISE', 'Clockwise'], ['ANTI_CLOCKWISE', 'Anti clockwise']]], v('direction_of_rotation') || 'CLOCKWISE') : ''}
      ${t.fields.map((f) => field(f, v(f[0]))).join('')}
      <div class="wide">${field(['remarks', 'Remarks', 'textarea'], v('remarks'))}</div>
    </div>
    ${p ? `<div class="note ok">Table ${esc(p.tableName)} · ${p.rowCount} row${p.rowCount === 1 ? '' : 's'} match serial ${esc(d.motor.serial_number)}${p.averageResistance !== undefined ? ` · R̄ = ${fmt(p.averageResistance)} from Electric Resistance` : ''}</div>
      ${resultsBlock(p.values, 'Preview of computed values')}${tableBlock(p.table, 'Preview of the load table')}`
      : done ? `${resultsBlock(t.results ? r : null, 'Stored values')}${tableBlock(k === 'performance_determination_test' ? d.parameters : null, 'Stored load table')}` : ''}
    <div class="actions"><button class="btn" type="submit" name="mode" value="preview" ${state.busy ? 'disabled' : ''}>Preview import</button>
      <button class="btn primary" type="submit" name="mode" value="save" ${state.busy ? 'disabled' : ''}>${done ? 'Re-import and save' : 'Import, save and mark completed'}</button></div></form>`;
}

/* ---------- render ---------- */
function render() {
  const inner = state.screen === 'login' ? views.login() : `<div class="shell">${sidebar()}<main class="content" data-screen="${state.screen}">${views[state.screen]()}</main></div>`;
  const active = document.activeElement; const focusId = active?.id; const sel = active?.selectionStart;
  root.innerHTML = inner + (state.toast ? `<div class="toast ${state.toast.kind}">${esc(state.toast.msg)}</div>` : '');
  if (focusId) { const el = document.getElementById(focusId); if (el) { el.focus(); if (sel !== undefined && el.setSelectionRange) try { el.setSelectionRange(sel, sel); } catch (_) { /* not a text input */ } } }
  if (state.screen === 'report' && state.reportTab === 'chart') drawChart();
  fitPreview();
}
// The report page is laid out at 910px + margins; scale it to the preview pane instead of cropping it.
function fitPreview() {
  const pane = document.querySelector('.preview'); const frame = pane?.querySelector('iframe'); if (!frame) return;
  const scale = Math.min(1, (pane.clientWidth - 44) / 980);
  frame.style.transform = `scale(${scale})`; pane.style.height = `${Math.round(1960 * scale) + 44}px`;
}
window.addEventListener('resize', fitPreview);

async function drawChart() {
  const canvas = document.getElementById('chart'); if (!canvas) return;
  const { series } = await api('chart.data', { id: state.motorId });
  if (chartInstance) chartInstance.destroy();
  // Config ported from templates/graph.html: fixed speed labels, five Y axes.
  const axis = (text, color, position) => ({ beginAtZero: true, type: 'linear', position, title: { display: true, text, color }, grid: { drawOnChartArea: false }, ticks: { font: { size: 16 } } });
  chartInstance = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels: [1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000], datasets: [
      { label: 'Torque', data: series.torque, tension: 0.4, yAxisID: 'torque' },
      { label: 'Amperes', data: series.amplitude, tension: 0.4, yAxisID: 'amplitude' },
      { label: 'Efficiency', data: series.efficiency, tension: 0.4, yAxisID: 'efficiency' },
      { label: 'Horsepower', data: series.horsePower, tension: 0.4, yAxisID: 'horsepower' },
      { label: 'Watts Out', data: series.wattsOut, tension: 0.4, yAxisID: 'watt' },
    ] },
    options: { responsive: true, maintainAspectRatio: false, animation: false, layout: { padding: 40 },
      plugins: { legend: { position: 'bottom', align: 'top', labels: { color: 'black', font: { size: 14 } } } },
      scales: { x: { title: { color: 'black', display: true, text: 'Speed[RPM]', font: { size: 16 } }, ticks: { font: { size: 16 } } },
        amplitude: axis(' Amps ', 'red', 'right'), horsepower: axis(' Horsepower ', 'blue', 'right'), watt: axis(' Watts Out ', 'pink', 'left'),
        efficiency: axis(' Efficiency ', 'green', 'left'), torque: axis('Torque[Ib.in] ', undefined, 'left') } },
  });
}

/* ---------- data loading ---------- */
async function loadMotors() { state.motors = await api('motors.list', { search: state.search }); }
async function loadMotor(id) {
  state.motorId = id; state.data = await api('motors.get', { id });
  state.mdbPaths = { ...state.data.settings.mdbPaths, ...Object.fromEntries(Object.entries(state.mdbPaths).filter(([, v]) => v)) };
  if (!state.test || !state.data.statuses[state.test]) state.test = ORDER.find((k) => state.data.statuses[k] === 'PENDING') || ORDER.find((k) => state.data.statuses[k]) || null;
}
async function go(screen) {
  await guard(async () => {
    if (screen === 'motors') { await loadMotors(); state.armed = null; }
    if (screen === 'workspace') await loadMotor(state.motorId);
    if (screen === 'report') { await loadMotor(state.motorId); state.reportHtml = await api('report.preview', { id: state.motorId }); }
    if (screen === 'settings') { state.settings = await api('settings.get'); state.users = await api('users.list'); state.info = await api('app.info'); }
    state.screen = screen; state.preview = null;
  });
  render();
}
const formData = (form) => Object.fromEntries(new FormData(form).entries());
const motorFromForm = (form) => {
  const fd = formData(form); const motor = {}; const tests = ORDER.map((k) => ({ test_type: k }));
  for (const [key, v] of Object.entries(fd)) {
    const [k, c] = key.split(':');
    if (c) tests.find((t) => t.test_type === k)[c] = true; else motor[key] = v;
  }
  return { motor, tests };
};

/* ---------- actions ---------- */
const actions = {
  go: (el) => go(el.dataset.screen),
  logout: () => { state.user = null; state.screen = 'login'; render(); },
  search: (el) => { state.search = el.value; clearTimeout(actions.t); actions.t = setTimeout(() => go('motors'), 200); },
  'new-motor': () => { state.motorId = null; state.data = null; state.screen = 'motor'; render(); },
  'edit-motor': () => { state.screen = 'motor'; render(); },
  open: async (el) => { state.motorId = Number(el.dataset.id); state.test = null; await go('workspace'); },
  report: async (el) => { state.motorId = Number(el.dataset.id); state.reportTab = 'report'; await go('report'); },
  delete: async (el) => {
    const id = Number(el.dataset.id);
    if (state.armed !== id) { state.armed = id; render(); setTimeout(() => { if (state.armed === id) { state.armed = null; render(); } }, 4000); return; }
    await guard(() => api('motors.remove', { id })); state.armed = null; await go('motors'); toast('Motor deleted');
  },
  'pick-test': (el) => { state.test = el.dataset.test; state.preview = null; state.draft = null; render(); },
  tab: async (el) => { state.reportTab = el.dataset.tab; render(); },
  'pick-mdb': async (el) => { const p = await guard(() => api('files.pickMdb')); if (p) { state.mdbPaths[el.dataset.test] = p; render(); } },
  'pick-folder': async () => { const p = await guard(() => api('files.pickFolder')); if (p) { await api('settings.set', { key: 'reports_dir', value: p }); await go('settings'); } },
  set: async (el) => { await guard(() => api('settings.set', { key: el.dataset.key, value: el.dataset.value || null })); await go('settings'); },
  'forget-mdb': async (el) => {
    const paths = JSON.parse(state.settings.mdb_paths || '{}'); delete paths[el.dataset.test]; delete state.mdbPaths[el.dataset.test];
    await guard(() => api('settings.set', { key: 'mdb_paths', value: JSON.stringify(paths) })); await go('settings');
  },
  'open-file': (el) => guard(() => api('files.open', { path: el.dataset.path })),
  'show-file': (el) => guard(() => api('files.showInFolder', { path: el.dataset.path })),
  'export-pdf': async () => {
    state.busy = true; render();
    const p = await guard(() => api('report.exportPdf', { id: state.motorId }));
    state.busy = false;
    if (p) { await loadMotor(state.motorId); toast(`PDF saved: ${p}`, 'ok'); } else render();
  },
  'save-png': async () => {
    const canvas = document.getElementById('chart'); if (!canvas) return;
    const p = await guard(() => api('files.saveChartPng', { serial: state.data.motor.serial_number, dataUrl: canvas.toDataURL('image/png') }));
    if (p) toast(`Chart saved: ${p}`, 'ok');
  },
  'remove-user': async (el) => {
    const id = Number(el.dataset.id);
    if (state.armed !== 'u' + id) { state.armed = 'u' + id; render(); return; }
    await guard(() => api('users.remove', { id })); state.armed = null; await go('settings');
  },
};
const submits = {
  login: async (form) => { const u = await guard(() => api('auth.login', formData(form))); if (u) { state.user = u; await go('motors'); } },
  'save-motor': async (form) => {
    const { motor, tests } = motorFromForm(form);
    const ok = await guard(async () => {
      if (state.motorId) { await api('motors.update', { id: state.motorId, motor, tests }); return true; }
      state.motorId = await api('motors.create', { userId: state.user.id, motor, tests }); return true;
    });
    if (ok) { state.test = null; await go('workspace'); toast('Motor saved', 'ok'); }
  },
  'save-manual': async (form) => {
    const r = await guard(() => api('tests.saveManual', { motorId: state.motorId, test: state.test, values: formData(form) }));
    if (r) { await loadMotor(state.motorId); toast(r.allCompleted ? 'Saved. All selected tests are completed.' : 'Saved and marked completed', 'ok'); }
  },
  import: async (form, submitter) => {
    const values = formData(form); const mode = submitter?.value || 'save'; const test = form.dataset.test;
    const payload = { motorId: state.motorId, test, dateStr: values.dateStr, mdbPath: state.mdbPaths[test], values };
    state.draft = { test, ...values };
    state.busy = true; render();
    const r = await guard(() => api(mode === 'preview' ? 'tests.importPreview' : 'tests.importSave', payload));
    state.busy = false;
    if (!r) { render(); return; }
    if (mode === 'preview') { state.preview = { ...r, test }; render(); return; }
    state.preview = null; state.draft = null; await loadMotor(state.motorId);
    toast(r.allCompleted ? 'Imported. All selected tests are completed.' : 'Imported and marked completed', 'ok');
  },
  'save-remarks': async (form) => { const ok = await guard(() => api('motors.saveRemarks', { id: state.motorId, ...formData(form) })); if (ok) { await go('report'); toast('Remarks saved', 'ok'); } },
  'save-scale': async (form) => { await guard(() => api('settings.set', { key: 'pdf_scale', value: formData(form).pdf_scale })); await go('settings'); toast('Print scale saved', 'ok'); },
  'add-user': async (form) => { const ok = await guard(() => api('users.create', formData(form))); if (ok) { await go('settings'); toast('User added', 'ok'); } },
  'change-password': async (form) => { const ok = await guard(() => api('auth.changePassword', { userId: state.user.id, ...formData(form) })); if (ok) { form.reset(); toast('Password changed', 'ok'); } },
};

root.addEventListener('click', (e) => {
  const el = e.target.closest('[data-action]'); if (!el || el.tagName === 'FORM' || el.tagName === 'INPUT') return;
  if (el.tagName === 'TR' && e.target.closest('button')) return;
  const fn = actions[el.dataset.action]; if (fn) { e.preventDefault(); fn(el, e); }
});
root.addEventListener('input', (e) => { const el = e.target; if (el.dataset.action === 'search') actions.search(el); });
root.addEventListener('submit', (e) => { const fn = submits[e.target.dataset.action]; if (fn) { e.preventDefault(); fn(e.target, e.submitter); } });
root.addEventListener('input', (e) => {
  if (!['f_resistance_ohm_1', 'f_resistance_ohm_2', 'f_resistance_ohm_3'].includes(e.target.id)) return;
  const [a, b, c] = [1, 2, 3].map((i) => parseFloat(document.getElementById(`f_resistance_ohm_${i}`)?.value) || 0);
  const u = document.getElementById('unbalance'); if (u) u.value = (Math.abs(a - b) + Math.abs(a - c) + Math.abs(b - c)).toFixed(3);
});

render();
