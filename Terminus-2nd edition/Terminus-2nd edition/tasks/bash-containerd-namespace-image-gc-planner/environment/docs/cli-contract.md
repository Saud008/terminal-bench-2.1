# ctrgc CLI contract

The ctrgc binary lives at /app/sbin/ctrgc and exposes scan-meta, resolve, and emit-plan.

scan-meta reads a metadata tree and writes /app/state/gc_snapshot.json.

resolve reads gc_snapshot.json and writes /app/state/eligibility.buffer using a caller-supplied epoch second for lease expiry comparison.

emit-plan reads eligibility.buffer only and writes /app/output/namespace_gc_plan.json in dry-run mode.
