CREATE TABLE IF NOT EXISTS samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  metric TEXT NOT NULL,
  labels TEXT NOT NULL,
  kind TEXT NOT NULL,
  value REAL NOT NULL,
  ts_ms INTEGER NOT NULL,
  scrape_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS histogram_buckets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  metric TEXT NOT NULL,
  labels TEXT NOT NULL,
  le TEXT NOT NULL,
  count REAL NOT NULL,
  ts_ms INTEGER NOT NULL,
  scrape_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_stats (
  lines_read INTEGER NOT NULL DEFAULT 0,
  samples_accepted INTEGER NOT NULL DEFAULT 0,
  scrapes_ingested INTEGER NOT NULL DEFAULT 0,
  cache_entries INTEGER NOT NULL DEFAULT 0,
  rollup_windows INTEGER NOT NULL DEFAULT 0,
  staleness_markers INTEGER NOT NULL DEFAULT 0
);

INSERT INTO ingest_stats (lines_read, samples_accepted, scrapes_ingested, cache_entries, rollup_windows, staleness_markers)
VALUES (0, 0, 0, 0, 0, 0);
