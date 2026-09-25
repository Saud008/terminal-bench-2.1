# Staging schema

Top-level fields: schema_version (1), bucket, inventory_fingerprint, objects (array), simulation (object or null).

Each object entry mirrors inventory fields plus current_version (bool) and noncurrent_since (ISO date or null).

simulation block after simulate: window_start, window_end, suppressed_keys (sorted), transitions_applied (sorted by key, version_id), expired_versions (sorted), delete_marker_orphan_count, simulation_digest.

Verifier-only fixtures mount at /opt/verifier-fixtures/s3lc_hidden. Duplicate-line ingest probes use /app/state/dup.jsonl and /app/state/dup.stage.json.
