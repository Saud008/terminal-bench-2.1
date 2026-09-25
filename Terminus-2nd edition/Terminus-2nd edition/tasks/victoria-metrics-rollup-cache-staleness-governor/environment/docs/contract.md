# vmrollup contract

All timestamps are UTC epoch milliseconds unless noted.

Scrape files use Prometheus text exposition. Each sample line is metric{labels} value [timestamp_ms]. Histogram lines use metric_bucket{le="..."} count.

Rollup windows align to rollup_interval_sec from /app/config/rollup.json using floor(ts_ms / interval_ms) * interval_ms in UTC.

On the query path, cache TTL expires when query_ms minus last_sample_ts_ms in the cache entry exceeds cache_ttl_sec times 1000. query_ms defaults per /app/docs/cli-surface.md. TTL must use the latest accepted sample timestamp in the window, not wall clock at ingest time.

Counter rate uses the maximum value in the window minus the value at window start, with counter reset detection per /app/docs/counter-reset.md.

Histogram rollup merges bucket counts per le label; the +Inf bucket must remain after bound shifts per /app/docs/histogram-merge.md.

Staleness markers propagate from raw tier to every downsample tier listed in config per /app/docs/rollup-snapshot.md.

Query must bypass cache when fresher raw samples exist within grace_window_sec of query time per /app/docs/staleness-grace.md.

Bundled fixtures under /app/fixtures/scrapes/ exercise vm_requests_total for counter rate, vm_cache_probe for cache TTL expiry, and vm_grace_total for grace bypass. Probe scrapes under /opt/tb3-probes/ reuse vm_requests_total for ingest smoke checks.
