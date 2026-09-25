# Scrape manifest

Path: /app/state/scrape-manifest.json

Fields:
- schema_version (int, always 1)
- scrapes_ingested (int)
- last_scrape_ts_ms (int)
- samples_accepted (int)
- cache_entries (int)
- rollup_windows_built (int) count of series rows written to rollup-snapshot.json after ingest. This must equal len(series) in that file. Count each tier row separately, so this value is not the same as cache_entries and is not a per-metric deduplicated count.
- staleness_markers (int)
- manifest_sha256 (hex sha256 of rollup-snapshot.json bytes after ingest)

Stats must reflect ingest_stats in SQLite after ingest completes, not live re-query at export time.
