# Shard map migration

Migration events are JSON lines with seq, op, shard_map path, and migration_id.

load_shard_map updates snapshot generation and shard_map_path from the referenced file. Cache is unchanged.

rollback reloads an earlier shard map file into the snapshot. On rollback the cache must be flushed entirely so no entry from a newer generation remains warm.

After migrate, rewrite /app/state/vindex-snapshot.json with updated generation, shard_map_path, migration_id, and cache contents.
