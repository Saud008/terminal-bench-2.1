# Export audit schema

routing-audit.json fields:

generation: snapshot generation after routing (must match snapshot file, not route plan generation alone).

snapshot_path: absolute path to the snapshot read for export.

route_count: number of routes in the plan.

cache_hit_count: cache hits recorded in the plan.

coalesce_dropped: dropped stale-generation entries during last ingest coalesce (zero if ingest did not run).

scatter_failures: count of batch queries whose scatter simulation failed (partial or full failure). This field is independent of route_count: when scatter_ok is false the route plan routes array is empty and scatter_failures is at least one. Do not infer scatter_failures from routes.length.

shard_counts: map shard name to route count.

Export reads the snapshot at snapshot_path; it does not re-parse wrap.go helpers.
