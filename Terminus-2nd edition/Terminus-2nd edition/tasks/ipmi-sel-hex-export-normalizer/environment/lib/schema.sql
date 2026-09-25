CREATE TABLE IF NOT EXISTS sel_records (
  rowid INTEGER PRIMARY KEY AUTOINCREMENT,
  record_id INTEGER NOT NULL,
  record_type INTEGER NOT NULL,
  ts INTEGER NOT NULL,
  generator_id INTEGER NOT NULL,
  sensor_type INTEGER NOT NULL,
  sensor_number INTEGER NOT NULL,
  event_type INTEGER NOT NULL,
  severity TEXT NOT NULL,
  sensor_name TEXT NOT NULL
);
