# Engineering problem contract — victoria-metrics-rollup-cache-staleness-governor

The vmrollup service has two coupled responsibilities that must stay consistent across ingest and query. Ingest builds durable rollup artifacts from Prometheus scrapes and records enough metadata for later cache decisions. Query must decide whether a cached rollup is still usable by comparing the cached window state with fresher raw samples and the configured grace window.

The core correctness requirement is that cache freshness is derived from data timestamps, not from when ingest happened to run. `last_sample_ts_ms` in the cache index is the source of truth for a window. Query must expire or bypass cached results when newer raw samples arrive inside the grace interval, even if the cached rollup was generated very recently.

Rollup bookkeeping must also stay internally consistent across output files. The scrape manifest, rollup snapshot, and cache index should describe the same ingest pass, with window counts, timestamps, and propagated staleness markers agreeing across artifacts. Query reports must then explain whether a result came from cache or a rebuild using the same timing rules described in the other contracts under `/app/docs/`.
