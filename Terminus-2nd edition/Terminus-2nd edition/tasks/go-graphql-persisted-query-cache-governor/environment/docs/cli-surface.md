# pqgov CLI surface

Binary path: /app/bin/pqgov

Fixed verb order for verifier pipelines:

1. ingest
2. reconcile
3. export-audit

## ingest

```
pqgov ingest --tenant TENANT --scenario SCENARIO [--fixture-dir DIR]
```

Reads manifests from DIR/tenants/SCENARIO/manifests/*.json sorted lexicographically by filename.
Validates operation hash binding and schema compatibility.
Writes the staging snapshot to /app/state/pq-staging.json

## reconcile

```
pqgov reconcile --tenant TENANT --scenario SCENARIO [--fixture-dir DIR]
```

Requires an existing /app/state/pq-staging.json from ingest for the same tenant and scenario
Updates /app/state/pq-ledger.db, writes /app/work/reconcile-report.json, and increments apq_audit_seq in /app/state/apq-audit-seq.json

Environment overrides:

- PQGOV_NOW_MS sets reconcile clock milliseconds.
- TB3_QUOTA_BIAS adjusts max_active from quotas.json (added to catalog value, floor at zero).
- TB3_TTL_BIAS adjusts ttl_ms from expiry.json (added to catalog value, floor at zero).
- TB3_COMPOUND_SCHEMA=1 requires compound schema_hash binding per schema-hash-contract.md.

## export-audit

```
pqgov export-audit --tenant TENANT --scenario SCENARIO [--output PATH]
```

Default output path: /app/output/pq-audit.sqlite

Refuses when apq_audit_seq is zero.
Copies ledger counts into pq_audit_export_meta and pq_audit_operations per audit-export-schema.md.
