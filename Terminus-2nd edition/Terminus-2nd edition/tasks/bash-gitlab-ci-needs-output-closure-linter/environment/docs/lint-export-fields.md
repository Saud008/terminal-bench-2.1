# Lint export fields

Export JSON contains run_id, findings array, summary counters, audit_digest. Findings include code, severity, job, message sorted by job then code. Finding codes include MATRIX_DUPLICATE, NEED_MISSING, STAGE_ORDER, and ARTIFACT_CLOSURE. audit_digest is sha256 of sorted finding codes plus summary totals. Export must read gclint-staging.json only, never re-parse ingest work files.
