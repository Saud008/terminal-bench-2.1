CREATE TABLE IF NOT EXISTS message_threads (
  message_id TEXT PRIMARY KEY,
  thread_root_id TEXT NOT NULL,
  date_unix INTEGER NOT NULL,
  subject TEXT NOT NULL,
  is_root INTEGER NOT NULL DEFAULT 0
);
