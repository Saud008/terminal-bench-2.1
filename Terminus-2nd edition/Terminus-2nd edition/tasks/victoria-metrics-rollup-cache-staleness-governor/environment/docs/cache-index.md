# Cache index

Path: /app/state/cache-index.json

Ingest writes one entry per raw-tier rollup window. Each entry includes:

- key: metric|labels|window_start_ms|window_end_ms
- metric (string)
- labels (string, empty when none)
- window_start_ms (int)
- window_end_ms (int)
- last_sample_ts_ms (int) latest accepted raw sample timestamp in the window

Keys must be unique. Distinct windows for the same metric must not share a key.
