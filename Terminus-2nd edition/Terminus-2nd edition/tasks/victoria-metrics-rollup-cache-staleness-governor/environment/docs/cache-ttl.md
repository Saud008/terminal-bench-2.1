# Cache TTL

Path: /app/state/cache-index.json

Each cache entry stores last_sample_ts_ms as the latest accepted raw sample timestamp for that metric, label set, and rollup window.

On query, a cache entry is expired when query_ms minus last_sample_ts_ms exceeds cache_ttl_sec times 1000.

query_ms defaults per /app/docs/cli-surface.md. Do not use host wall clock when --query-ms is omitted.

When expired or bypassed by grace per /app/docs/staleness-grace.md, served_from_cache must be false and rollup must be rebuilt from SQLite samples.
