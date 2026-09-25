# Export report schema

Path: /app/output/sssd-cache-report.json

Export reads /app/state/sssd-cache-snapshot.json only. It must not re-parse operation logs.

Fields:

- domain_suffix: copied from snapshot
- active_negatives: negatives from snapshot where expires_at is strictly greater than evaluated_at_ms
- positives: copied from snapshot positives array
- stats: copied from snapshot stats

Expired negatives must not appear in active_negatives even if still listed in the snapshot negatives array.

SQLite persistence at ingest must store only active negatives using the same expires_at versus evaluated_at_ms rule.
