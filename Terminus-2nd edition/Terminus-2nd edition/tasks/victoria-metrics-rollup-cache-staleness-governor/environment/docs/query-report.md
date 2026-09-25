# Query report

Path: passed to --output on query, default /app/output/query-report.json

Fields:

- metric (string)
- query_ms (int) evaluation clock used for TTL and grace
- served_from_cache (bool)
- fresh_raw_within_grace (bool)
- rollup (object) rebuilt or cached rollup row for the requested metric and window

query_ms must echo the value used for the decision, including the generated_at_ms plus 1000 default from /app/docs/cli-surface.md when --query-ms is omitted.
