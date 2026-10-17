// Runs inside the renderer (via executeJavaScript) when the app starts with --smoke. Drives the real UI.
(async () => {
  const log = [];
  try {
  const $ = (q) => document.querySelector(q);
  $('#f_username').value = 'admin'; $('#f_password').value = 'admin';
  await submits.login($('form[data-action=login]'));
  log.push('login→' + state.screen);
  state.screen = 'motor'; state.motorId = null; state.data = null; render();
  const mf = $('form[data-action=save-motor]');
  mf.serial_number.value = 'SMOKE-1'; mf.customer_name.value = 'Acme Motors'; mf.sales_order_number.value = 'SO-1'; mf.power.value = '45'; mf.director_cerad.value = 'Dr. A'; mf.lab_instructor.value = 'Engr. B';
  mf.querySelector('[name="electric_resistance_test:routine"]').checked = true;
  mf.querySelector('[name="withstand_voltage_ac_test:type"]').checked = true;
  mf.querySelector('[name="lock_rotor_test:special"]').checked = true;
  mf.querySelector('[name="performance_determination_test:routine"]').checked = true;
  mf.querySelector('[name="no_load_test:routine"]').checked = true;
  await submits['save-motor'](mf);
  log.push('create→' + state.screen + ' sideItems=' + document.querySelectorAll('.side .item').length + ' first=' + state.test);
  const f = $('form[data-action=save-manual]'); f.resistance_ohm_1.value = '0.3'; f.resistance_ohm_2.value = '0.31'; f.resistance_ohm_3.value = '0.29'; f.remarks.value = 'fine';
  await submits['save-manual'](f);
  log.push('electric=' + state.data.statuses.electric_resistance_test + ' unbalance=' + state.data.results.electric_resistance_test.unbalance_percentage);
  state.test = 'withstand_voltage_ac_test'; render();
  const f2 = $('form[data-action=save-manual]'); f2.description.value = 'Hi-pot'; f2.voltage_kv.value = '2'; f2.time_in_seconds.value = '60';
  await submits['save-manual'](f2);
  state.test = 'lock_rotor_test'; render();
  const f3 = $('form[data-action=import]'); f3.dateStr.value = '2024-03-06';
  await submits.import(f3, { value: 'preview' });
  log.push('importNoFile→toast=' + JSON.stringify(state.toast && state.toast.msg));
  state.mdbPaths.performance_determination_test = 'perf.mdb'; state.mdbPaths.no_load_test = 'noload.mdb'; state.mdbPaths.lock_rotor_test = 'noload.mdb';
  state.test = 'performance_determination_test'; render();
  const fp = $('form[data-action=import]'); fp.dateStr.value = '2024-03-06'; fp.voltage.value = '400'; fp.frequency.value = '50'; fp.nominal_t.value = '290';
  await submits.import(fp, { value: 'preview' });
  log.push('perfPreview rows=' + state.preview.rowCount + ' table=' + state.preview.table.length + ' domRows=' + document.querySelectorAll('form[data-action=import] tbody tr').length + ' status=' + state.data.statuses.performance_determination_test);
  await submits.import($('form[data-action=import]'), { value: 'save' });
  log.push('perfSaved status=' + state.data.statuses.performance_determination_test + ' params=' + state.data.parameters.length + ' eff100=' + state.data.parameters[9].efficiency.toFixed(2));
  state.test = 'no_load_test'; render(); const fn = $('form[data-action=import]'); fn.dateStr.value = '2024-03-06'; fn.direction_of_rotation.value = 'ANTI_CLOCKWISE';
  await submits.import(fn, { value: 'save' });
  state.test = 'lock_rotor_test'; render(); const fl = $('form[data-action=import]'); fl.dateStr.value = '2024-03-06'; fl.vibration.value = '1.2'; fl.noise.value = '70'; fl.temperature.value = '41';
  await submits.import(fl, { value: 'save' });
  log.push('allCompleted=' + state.data.allCompleted + ' noLoadV=' + state.data.results.no_load_test.voltage.toFixed(1) + ' lockHz=' + state.data.results.lock_rotor_test.speed);
  await go('report');
  log.push('report html=' + state.reportHtml.length + ' iframe=' + !!$('iframe') + ' sections=' + (state.reportHtml.match(/class="title">3\./g) || []).length);
  state.reportTab = 'chart'; render(); await new Promise((r) => setTimeout(r, 300));
  log.push('chartTab canvas=' + !!$('#chart') + ' datasets=' + (chartInstance ? chartInstance.data.datasets.length : 0) + ' points=' + (chartInstance ? chartInstance.data.datasets[0].data.length : 0));
  await go('settings'); log.push('settings users=' + state.users.length + ' version=' + state.info.version);
  await go('motors'); log.push('motors rows=' + document.querySelectorAll('tbody tr').length);
  } catch (e) { log.push('ERR ' + e.message + ' toast=' + JSON.stringify(state.toast && state.toast.msg) + ' screen=' + state.screen); }
  return log.join(' | ');
})();
