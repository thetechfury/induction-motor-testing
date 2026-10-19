'use strict';
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const { openDb } = require('./src/db');
const { createServices } = require('./src/services');
const { readMdbTable } = require('./src/mdb');
const { exportPdf } = require('./src/pdf');

const SMOKE = process.argv.includes('--smoke');
if (SMOKE) { const tmp = path.join(require('node:os').tmpdir(), 'motor-lab-smoke-' + Date.now()); app.setPath('userData', tmp); app.setPath('documents', tmp); }
let win;
let services;
let handlers;

const asset = (f) => path.join(__dirname, 'assets', f);
const reportAssets = (print) => ({
  css: fs.readFileSync(asset('report/induction_report.css'), 'utf8'),
  logoDataUri: 'data:image/png;base64,' + fs.readFileSync(asset('report/logo.png')).toString('base64'),
  print,
});
const safeName = (s) => String(s).replace(/[\\/:*?"<>|]+/g, '_').trim();

function createWindow() {
  win = new BrowserWindow({
    width: 1280, height: 840, minWidth: 980, minHeight: 640, show: false,
    title: 'Induction Motor Testing', backgroundColor: '#f4f6f9',
    icon: asset('icons/icon-1024.png'),
    webPreferences: { preload: path.join(__dirname, 'preload.js'), sandbox: true, contextIsolation: true },
  });
  if (app.isPackaged) win.setMenuBarVisibility(false);
  if (process.platform === 'darwin' && !app.isPackaged) app.dock.setIcon(asset('icons/icon-1024.png')); // dev run otherwise shows Electron's icon
  win.once('ready-to-show', () => win.show());
  win.loadFile('renderer/index.html');
}

app.whenReady().then(() => {
  const userData = app.getPath('userData');
  fs.mkdirSync(userData, { recursive: true });
  const db = openDb(path.join(userData, 'motor-lab.sqlite'));
  services = createServices({ db, readMdbTable: SMOKE ? require('./test/fixtures/mdb-rows') : readMdbTable });
  const defaultReportsDir = path.join(app.getPath('documents'), 'Motor Testing Reports');
  const reportsDir = () => services['settings.get']().reports_dir || defaultReportsDir;

  handlers = {
    ...services,
    'app.info': () => ({ version: app.getVersion(), dbPath: path.join(userData, 'motor-lab.sqlite'), reportsDir: reportsDir() }),
    'report.preview': ({ id }) => services['report.html']({ id, assets: reportAssets(false) }),
    'report.exportPdf': async ({ id }) => {
      const { motor } = services['report.data']({ id });
      const outPath = path.join(reportsDir(), safeName(`${motor.customer_name}-${motor.serial_number}.pdf`));
      // shortcut: 0.74 fits the 910px template on A4 like wkhtmltopdf's smart shrinking; adjust in Settings if the page break moves
      const scale = Number(services['settings.get']().pdf_scale) || 0.74;
      await exportPdf({ html: services['report.html']({ id, assets: reportAssets(true) }), outPath, tmpHtml: path.join(userData, 'report-print.html'), scale });
      services['report.setLink']({ id, link: outPath });
      return outPath;
    },
    'files.pickMdb': async () => {
      const r = await dialog.showOpenDialog(win, { title: 'Choose the instrument .mdb file', properties: ['openFile'], filters: [{ name: 'Access database', extensions: ['mdb', 'accdb'] }] });
      return r.canceled ? null : r.filePaths[0];
    },
    'files.pickFolder': async () => {
      const r = await dialog.showOpenDialog(win, { title: 'Choose where PDF reports are saved', properties: ['openDirectory', 'createDirectory'] });
      return r.canceled ? null : r.filePaths[0];
    },
    'files.open': ({ path: p }) => shell.openPath(p),
    'files.showInFolder': ({ path: p }) => { shell.showItemInFolder(p); return true; },
    'files.saveChartPng': async ({ serial, dataUrl }) => {
      const r = await dialog.showSaveDialog(win, { defaultPath: path.join(app.getPath('pictures'), `${safeName(serial)}-motor-chart.png`), filters: [{ name: 'PNG image', extensions: ['png'] }] });
      if (r.canceled) return null;
      fs.writeFileSync(r.filePath, Buffer.from(String(dataUrl).split(',')[1], 'base64'));
      return r.filePath;
    },
  };

  ipcMain.handle('api', async (_e, name, payload) => {
    const fn = handlers[name];
    if (!fn) return { ok: false, error: `Unknown call ${name}` };
    try { return { ok: true, data: await fn(payload || {}) }; } catch (err) { return { ok: false, error: err.message }; }
  });

  createWindow();
  if (SMOKE) {
    const errors = [];
    win.webContents.on('console-message', (ev, level, message) => { const lvl = ev.level ?? level; if (lvl === 'error' || lvl >= 2) errors.push(ev.message ?? message); });
    win.webContents.once('did-finish-load', async () => {
      try {
        const log = await win.webContents.executeJavaScript(fs.readFileSync(path.join(__dirname, 'test', 'smoke-ui.js'), 'utf8'));
        const id = (await handlers['motors.list']({}))[0].id;
        const pdf = await handlers['report.exportPdf']({ id });
        fs.writeFileSync(path.join(userData, 'report-print-full.html'), handlers['report.preview']({ id }));
        if (process.env.SMOKE_SHOTS) { // screenshots of each screen for visual review
          const steps = [['motors', "go('motors')"], ['workspace', "(async () => { state.motorId = (await api('motors.list', {}))[0].id; state.test = 'performance_determination_test'; await go('workspace'); })()"],
            ['report', "(async () => { state.reportTab = 'report'; await go('report'); })()"], ['chart', "(async () => { state.reportTab = 'chart'; render(); await new Promise((r) => setTimeout(r, 600)); })()"], ['settings', "go('settings')"], ['form', "(async () => { state.screen = 'motor'; render(); })()"], ['login', "(async () => { state.user = null; state.screen = 'login'; render(); })()"]];
          for (const [name, js] of steps) { await win.webContents.executeJavaScript(js); await new Promise((r) => setTimeout(r, 500)); fs.writeFileSync(path.join(process.env.SMOKE_SHOTS, `shot-${name}.png`), (await win.capturePage()).toPNG()); }
        }
        console.log(`SMOKE ${log} | pdf=${fs.statSync(pdf).size}B ${pdf} | rendererErrors=${JSON.stringify(errors)}`);
      } catch (e) { console.log('SMOKE FAILED', e.message, JSON.stringify(errors), await win.webContents.executeJavaScript('document.body.innerHTML.slice(0,400)')); }
      app.quit();
    });
  }
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
