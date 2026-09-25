# Staleness grace

grace_window_sec in config defines how recently a raw sample may arrive and still force query to bypass cache.

query_ms is defined in /app/docs/cli-surface.md. Grace comparisons always use query_ms, never the host wall clock.

A raw sample is fresher than the cache entry when its ts_ms is strictly greater than cache_entry.last_sample_ts_ms. Equal timestamps are not fresher.

A fresher raw sample is inside the grace interval when (query_ms - ts_ms) is less than or equal to grace_window_sec times 1000.

On query, if any raw sample for the requested metric and window is fresher and inside the grace interval, fresh_raw_within_grace must be true, served_from_cache must be false, and rollup must be rebuilt from SQLite samples.

served_from_cache true only when no fresher raw sample exists inside the grace interval.
