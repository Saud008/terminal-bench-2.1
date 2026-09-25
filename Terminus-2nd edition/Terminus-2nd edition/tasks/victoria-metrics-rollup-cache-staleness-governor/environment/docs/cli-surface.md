# CLI surface

vmrollup ingest --scrape-dir PATH --config PATH --db PATH

vmrollup query --metric NAME --window-start-ms MS --window-end-ms MS --config PATH --db PATH --output PATH [--query-ms MS]

ingest exits 1 when --scrape-dir is missing or unreadable.

ingest writes /app/state/cache-index.json with one entry per rollup window keyed per /app/docs/cache-ttl.md.

query reads rollup series from /app/state/rollup-snapshot.json and cache entries from /app/state/cache-index.json.

query_ms is the evaluation clock for TTL and grace on the query path. When --query-ms is omitted, default query_ms to rollup-snapshot.json generated_at_ms plus 1000. Do not use the host wall clock when --query-ms is omitted. The query report must echo the query_ms value used.

When --query-ms is set explicitly, TTL and grace decisions use that timestamp.
