# Window overlap weighting

Each shard carries window_start_ms and window_end_ms inclusive-exclusive bounds on event time. Before conservative merge, compute the intersection window across all shards in the bundle:

intersection_start = max(shard.window_start_ms)
intersection_end = min(shard.window_end_ms)
overlap_ms = max(0, intersection_end - intersection_start)

When overlap_ms equals zero, ingest must reject the bundle atomically with no staging artifact, matching the compatibility gate failure semantics.

For each shard i with window duration window_ms_i = window_end_ms - window_start_ms, the overlap weight is weight_i = overlap_ms / window_ms_i as floating point. Merge scales every counter cell of shard i by floor(cell * weight_i) before cell-wise max aggregation.

The staging snapshot records overlap_ms and a window_weights map keyed by shard_id per /app/docs/merge-stage-schema.md.
