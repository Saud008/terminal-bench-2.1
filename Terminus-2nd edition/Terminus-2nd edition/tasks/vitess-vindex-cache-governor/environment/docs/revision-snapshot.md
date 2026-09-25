# Snapshot contract

/app/state/vindex-snapshot.json is the staging artifact between ingest and route/export.

Fields: generation (int), shard_map_path (absolute path string), vindexes (array), cache (array of cache entries), migration_id (string), coalesce_dropped (int count of cache rows removed during the last ingest coalesce because their generation did not match the ingested shard map).

Array fields such as vindexes and cache must serialize as JSON arrays. An empty array must be written as [], never null.

Ingest sets coalesce_dropped when optional cache seed rows are dropped. Export copies this value into routing-audit.json per export-schema.md.

Ingest must create this file. Route and export read it. Tests assert the snapshot exists after ingest and matches independent reference parsing of shard map and vindex catalog inputs.
