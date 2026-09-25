# Audit export schema

Output default: /app/output/pq-audit.sqlite

SQLite database with tables:

## pq_audit_export_meta

Single row per export.

Columns:

- tenant_id
- scenario
- schema_hash
- active_count (SELECT COUNT(*) FROM pq_operations WHERE status='active' in source ledger)
- evicted_count (SELECT COUNT(*) WHERE status='evicted')
- quota_max (from reconcile report quota_max)
- export_revision (apq_audit_seq at export time)

## pq_audit_operations

One row per ledger operation (active and evicted) copied from /app/state/pq-ledger.db with columns operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms.

Export must read counts from the ledger database, not from staging operation_count.

An optional sidecar meta JSON file beside the SQLite export is not part of the verifier contract.
