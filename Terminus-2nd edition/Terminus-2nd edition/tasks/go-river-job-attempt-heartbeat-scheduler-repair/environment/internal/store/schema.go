package store

const schemaSQL = `
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  priority INTEGER NOT NULL,
  state TEXT NOT NULL,
  attempts INTEGER NOT NULL,
  max_attempts INTEGER NOT NULL,
  available_at_ms INTEGER NOT NULL,
  created_at_ms INTEGER NOT NULL,
  finished_at_ms INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS leases (
  job_id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL,
  expires_at_ms INTEGER NOT NULL,
  heartbeat_at_ms INTEGER NOT NULL
);
`
