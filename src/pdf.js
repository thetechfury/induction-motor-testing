'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { BrowserWindow } = require('electron');

// Renders the report HTML in a hidden window and prints it with Chromium. Replaces wkhtmltopdf.
async function exportPdf({ html, outPath, tmpHtml, scale }) {
  fs.writeFileSync(tmpHtml, html);
  const win = new BrowserWindow({ show: false, webPreferences: { sandbox: true, contextIsolation: true } });
  try {
    await win.loadFile(tmpHtml);
    const pdf = await win.webContents.printToPDF({ pageSize: 'A4', printBackground: true, preferCSSPageSize: true, scale });
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, pdf);
  } finally {
    win.destroy();
  }
  return outPath;
}

module.exports = { exportPdf };
