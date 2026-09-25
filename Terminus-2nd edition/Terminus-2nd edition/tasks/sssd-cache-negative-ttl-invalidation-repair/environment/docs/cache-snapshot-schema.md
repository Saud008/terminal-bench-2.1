# Staging snapshot schema

Path: /app/state/sssd-cache-snapshot.json

Fields:

- snapshot_version: integer, always 1
- domain_suffix: string from config at ingest time
- evaluated_at_ms: last operation ts applied during replay
- negatives: array of {domain, name, miss_ts, expires_at} sorted by canonical key order
- positives: array of {domain, name, value} sorted by canonical key order
- groups: array of {group, members[]} sorted by group name; members sorted lexicographically
- stats: replay counters including lines_read, ops_applied, negative_refreshed, group_invalidations, wal_checkpoints

The snapshot records full in-memory state after replay, including expired negative rows. Export and SQLite persistence apply separate active filters documented in export-report-schema.md.
