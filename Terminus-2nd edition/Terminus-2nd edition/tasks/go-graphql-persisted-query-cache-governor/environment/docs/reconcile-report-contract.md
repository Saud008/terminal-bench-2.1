# Reconcile report contract

Path: /app/work/reconcile-report.json

Compact JSON sorted keys trailing newline.

Fields:

- tenant_id
- scenario
- schema_hash (from staging)
- active_count (ledger rows status active)
- evicted_count (ledger rows status evicted)
- quota_max (effective max_active after bias)
- quota_headroom
- apq_audit_seq (matches /app/state/apq-audit-seq.json after increment)

Each reconcile pass increments apq_audit_seq by exactly one on success.

export-audit requires apq_audit_seq > 0.
