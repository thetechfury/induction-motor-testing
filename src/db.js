'use strict';
const { DatabaseSync } = require('node:sqlite');

// Mirrors motor_testing/models.py. One-to-one result tables use motor_id as their primary key.
const RESULT_TABLES = {
  electric_resistance_tests: 'resistance_ohm_1 REAL, resistance_ohm_2 REAL, resistance_ohm_3 REAL, ambient_temperature_C REAL, unbalance_percentage REAL',
  temperature_rise_tests: 'voltage REAL, winding REAL, frequency REAL, de_bearing REAL, nde_bearing REAL',
  performance_determination_tests: 'voltage REAL, frequency REAL, nominal_t REAL, is_current_date INTEGER DEFAULT 0, test_date TEXT, table_name TEXT, report_date TEXT, mdb_data TEXT',
  no_load_tests: "voltage REAL, current REAL, power REAL, frequency REAL, speed REAL, direction_of_rotation TEXT DEFAULT 'CLOCKWISE', report_date TEXT, mdb_data TEXT, reported_date TEXT",
  withstand_voltage_ac_tests: 'description TEXT, voltage_kv REAL, time_in_seconds INTEGER',
  insulation_resistance_tests: 'description TEXT, voltage REAL, insulation_resistance REAL, time_in_seconds INTEGER, ambient_temperature_C REAL, humidity_percentage REAL',
  lock_rotor_tests: 'vibration REAL, noise REAL, temperature REAL, speed REAL, voltage REAL, current REAL, power REAL, report_date TEXT, mdb_data TEXT, reported_date TEXT',
};

const SCHEMA = `
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, salt TEXT NOT NULL, password_hash TEXT NOT NULL,
  created_on TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS motors (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id),
  serial_number TEXT NOT NULL, customer_name TEXT NOT NULL, sales_order_number TEXT NOT NULL,
  director_cerad TEXT NOT NULL DEFAULT '', lab_instructor TEXT NOT NULL DEFAULT '',
  tag TEXT, material TEXT, frame TEXT, mounting TEXT, drawing TEXT, enclosure TEXT, altitude_M INTEGER,
  duty_cycle TEXT, design TEXT, insulation_class TEXT, temperature_rise_K REAL, ambient_temperature_C REAL, service_factor REAL,
  voltage INTEGER, current INTEGER, power INTEGER NOT NULL, frequency INTEGER, speed INTEGER, p_f REAL, efficiency REAL,
  status TEXT NOT NULL DEFAULT 'ACTIVE', report_link TEXT, remarks TEXT, test_type TEXT NOT NULL DEFAULT '45kw',
  created_on TEXT NOT NULL DEFAULT (datetime('now')), updated_on TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS performance_tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, motor_id INTEGER NOT NULL REFERENCES motors(id) ON DELETE CASCADE,
  test_type TEXT NOT NULL, routine INTEGER, type INTEGER, special INTEGER, page_number INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL, UNIQUE(motor_id, test_type));
CREATE TABLE IF NOT EXISTS performance_test_parameters (
  id INTEGER PRIMARY KEY AUTOINCREMENT, motor_id INTEGER NOT NULL REFERENCES motors(id) ON DELETE CASCADE,
  load INTEGER, current REAL, slip REAL, speed REAL, efficiency REAL, cos REAL);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
` + Object.entries(RESULT_TABLES).map(([name, cols]) => `
CREATE TABLE IF NOT EXISTS ${name} (
  motor_id INTEGER PRIMARY KEY REFERENCES motors(id) ON DELETE CASCADE, ${cols}, remarks TEXT,
  created_on TEXT NOT NULL DEFAULT (datetime('now')), updated_on TEXT NOT NULL DEFAULT (datetime('now')));`).join('');

function openDb(file) {
  const db = new DatabaseSync(file);
  db.exec('PRAGMA foreign_keys = ON;');
  db.exec(SCHEMA);
  return db;
}

module.exports = { openDb, RESULT_TABLES };
