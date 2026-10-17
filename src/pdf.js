'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { BrowserWindow } = require('electron');

// One hidden window is reused for every export: Chromium fails every load (ERR_FAILED) in a second hidden
// window created after the first one was destroyed, so the window lives as long as the app.
let printWin = null;
const win = () => {
  if (!printWin || printWin.isDestroyed()) printWin = new BrowserWindow({ show: false, webPreferences: { sandbox: true, contextIsolation: true } });
  return printWin;
};

// Renders the report HTML and prints it with Chromium. Replaces wkhtmltopdf.
async function exportPdf({ html, outPath, tmpHtml, scale }) {
  const file = tmpHtml.replace(/\.html$/, `-${process.pid}.html`);
  fs.writeFileSync(file, html);
  try {
    const w = win();
    await w.loadFile(file);
    const pdf = await w.webContents.printToPDF({ pageSize: 'A4', printBackground: true, preferCSSPageSize: true, scale });
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, pdf);
  } finally {
    fs.rmSync(file, { force: true });
  }
  return outPath;
}

module.exports = { exportPdf };
