package store

const schemaSQL = `
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tuples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  namespace TEXT NOT NULL,
  object TEXT NOT NULL,
  relation TEXT NOT NULL,
  subject TEXT NOT NULL,
  caveat_expr TEXT,
  created_revision INTEGER NOT NULL,
  tombstone_revision INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tuples_ns ON tuples(namespace);
CREATE INDEX IF NOT EXISTS idx_tuples_lookup ON tuples(namespace, object, relation, subject);

CREATE TABLE IF NOT EXISTS revision_log (
  revision INTEGER PRIMARY KEY,
  namespace TEXT NOT NULL,
  op TEXT NOT NULL,
  object TEXT NOT NULL,
  relation TEXT NOT NULL,
  subject TEXT NOT NULL,
  ts INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_revision_log_ns ON revision_log(namespace);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tuples_natural
  ON tuples(namespace, object, relation, subject);
`
