# Submission explanations — vitess-vindex-cache-governor

**Task folder:** tasks/vitess-vindex-cache-governor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must align five interacting Go modules so vtgatesim ingest, route, migrate, and export all honor contracts spread across cache-coalesce, vindex-contract, scatter-planner, and export-schema docs. Typed cache keys must include the vindex type prefix, generation must gate both coalesce and lookup, and binary keys need right-aligned big-endian uint64 padding rather than the broken little-endian shortcut. Partial scatter faults on binary keys ending in ff must fail routing without resurrecting stale cache rows from an optional seed file. Rollback migrations must flush warm cache state so generation-2 entries cannot influence generation-1 routes after resharding events.

## Solution Explanation

The oracle copies five corrected Go sources into /app/internal (hasher, lookup cache, scatter planner, migration hook, and ingest stage), then rebuilds vtgatesim from /app/cmd/vtgatesim. SpaceKey and ResolveShard follow FNV-1a and inclusive-start exclusive-end shard ranges using vindex type names. Cache lookup uses typed key_hex values, coalesce filters seed rows to the active shard-map generation, and scatter simulation failures invalidate matching slots instead of returning prior shards. Rollback events call store.Flush and clear snapshot cache arrays before routing resumes.

## Verification Explanation

Pytest rebuilds the Go binary in test.sh before every case, then drives vtgatesim ingest, route, migrate, and export through subprocess calls with independent reference_routes math in Python. Nineteen behavioral tests cover staging snapshot fields, mixed vindex batches, coalesce_dropped accounting, scatter failure export counts, rollback cache flush, and duplicate-key cache hits within one batch. A hidden TB3 fixture batch under /opt/verifier-fixtures proves hash and lookup vindexes with the same display key route to different shards when typed cache keys are correct. Export audit assertions verify snapshot_path, generation alignment, and scatter_failures semantics without reading wrap.go decoys. Fresh-output paths under /app/state and /app/output are reset between tests so agents cannot pass by reusing prebuilt JSON artifacts from the image layer.
