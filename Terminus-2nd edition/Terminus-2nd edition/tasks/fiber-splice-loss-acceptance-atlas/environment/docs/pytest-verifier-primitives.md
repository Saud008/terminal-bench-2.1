# Pytest verifier primitives

Tests invoke /app/bin/fsplatlas through subprocess and recompute acceptance using tests/splice_refmath.py helpers.
The splice_refmath module and hashlib mirror /app/tools/audit_digest_ref.py for audit_digest cross-checks.

Workspace paths exercised by pytest include /app/state/capture-cache/, /app/work/reflection-buffer/, /app/work/topology-snapshot/, /app/output/, /app/scripts/reset-workspace.sh, and /app/fixtures/.
TB3_TRACE_ROOT redirects fixture roots for hidden traps under /opt/verifier-fixtures/fsplatlas/.
TB3_LOSS_THRESHOLD_DB and TB3_REFLECTION_TOLERANCE_M override manifest thresholds during scan-reflections.
