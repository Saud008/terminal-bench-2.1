# Fixture catalog

Bundled under /app/fixtures/:

shardmaps/base-gen1.json — generation 1 two-shard layout.

shardmaps/reshard-gen2.json — generation 2 three-shard layout.

shardmaps/rollback-gen1.json — generation 1 layout used after rollback.

vindexes/catalog.json — hash, binary, lookup vindexes.

batches/mixed-types.json — multi-vindex smoke batch.

batches/scatter-trap.json — binary key triggering partial scatter.

cache-seed/stale-gen2.json — seed cache with generation 2 entry for coalesce trap.

events/rollback-warm.jsonl — reshard then rollback sequence.

Hidden verifier inputs may appear only under /opt/verifier-fixtures/ when TB3_VINDEX_FIXTURES is set to that directory.
