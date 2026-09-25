CREATE TABLE IF NOT EXISTS messages (
  message_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  maildir_relpath TEXT NOT NULL,
  flags TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  keywords_source TEXT NOT NULL,
  mtime_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
