# Export schema

Path: /app/output/authz-report.json

Produced by POST /v1/export via internal/export/publish.go.

## Fields

- generated_revision — head revision at export time
- snapshot_revision — revision read from /app/state/revision-snapshot.json
- namespace_counts — map of namespace to active tuple count in snapshot
- allowed_checks — probe summaries that evaluated true
- denied_checks — probe summaries that evaluated false
- tuple_total — tuple_count from snapshot

## Probe checks

Export evaluates fixed probes:

- doc/plan viewer for user:alice (transitive via group:eng)
- doc/plan viewer for user:bob (direct tuple with caveat)

Results use closure cache and caveat evaluator at snapshot_revision.

## Regeneration

Export overwrites the file atomically. Clients should read generated_revision and snapshot_revision together to detect skew.
