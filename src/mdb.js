'use strict';
const fs = require('node:fs');

// Reads one table of an MS-Access file as arrays in column order (what pyodbc returned to the Django code).
async function readMdbTable(filePath, tableName) {
  const { default: MDBReader } = await import('mdb-reader');
  const reader = new MDBReader(fs.readFileSync(filePath));
  const wanted = String(tableName).toLowerCase();
  const name = reader.getTableNames().find((n) => n.toLowerCase() === wanted);
  if (!name) throw new Error(`Table ${tableName} not found`);
  const table = reader.getTable(name);
  const cols = table.getColumnNames();
  return table.getData().map((row) => cols.map((c) => {
    const v = row[c];
    if (v instanceof Date) return v.toISOString();
    if (typeof v === 'bigint') return Number(v);
    if (Buffer.isBuffer(v)) return v.toString('base64');
    return v;
  }));
}

module.exports = { readMdbTable };
