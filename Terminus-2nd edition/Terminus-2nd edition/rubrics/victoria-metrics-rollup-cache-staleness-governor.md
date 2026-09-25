# Platform rubric — victoria-metrics-rollup-cache-staleness-governor

**Task folder:** tasks/victoria-metrics-rollup-cache-staleness-governor/

Agent implements ingest that writes /app/state/scrape-manifest.json, rollup-snapshot.json, and cache-index.json per scrape-manifest and cache-index contracts, +3
Agent applies counter reset detection mid-window so rate_per_sec matches reference math after a decreasing counter sample, +3
Agent merges histogram buckets preserving the +Inf le count when bucket bounds shift between scrapes, +2
Agent propagates stale markers from raw tier to every configured downsample tier in rollup-snapshot.json, +2
Agent expires cache entries on query using query_ms minus last_sample_ts_ms rather than ingest wall clock, +3
Agent defaults omitted --query-ms to rollup-snapshot generated_at_ms plus 1000 and echoes that value in query-report.json, +2
Agent bypasses cache when fresher raw samples arrive inside grace_window_sec of query_ms per staleness-grace.md, +3
Agent rebuilds rollup rows from SQLite when cache TTL expires instead of serving stale snapshot values, +2
Agent writes distinct cache-index keys per metric labels and aligned window per cache-ttl.md, +2
Agent patches only histogram merge while leaving query_ms default or grace bypass broken, -3
Agent uses host wall clock when --query-ms is omitted instead of generated_at_ms plus 1000, -3
Agent serves cached rollup after TTL expiry without rebuilding from raw samples, -2
Agent drops +Inf histogram bucket after le bound shifts, -2
Agent ignores counter reset and reports negative rate across reset boundary, -3
