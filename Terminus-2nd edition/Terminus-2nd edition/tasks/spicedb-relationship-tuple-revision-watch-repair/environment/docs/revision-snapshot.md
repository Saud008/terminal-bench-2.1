# Revision snapshot schema

Path: /app/state/revision-snapshot.json

Written by internal/ingest/stage.go after every tuple write and namespace prefix delete.

## Top-level fields

- revision — revision number captured in this snapshot
- tuple_count — active tuple count at revision
- namespaces — sorted distinct namespace strings with active tuples
- tuples — array of snapshot tuple rows
- check_summaries — embedded probe results used when check falls back to stale snapshot

## Snapshot tuple row

- namespace, object, relation, subject
- caveat_expr — optional JSON string or omitted
- active — boolean; false when tombstoned at or before snapshot revision

## Staleness

Check compares head revision against token revision using watch_stale_lag_threshold. When within threshold per /app/docs/check-contract.md, check may read check_summaries from this file instead of live store evaluation.

Snapshots are authoritative for export: /app/output/authz-report.json uses snapshot revision as snapshot_revision.
