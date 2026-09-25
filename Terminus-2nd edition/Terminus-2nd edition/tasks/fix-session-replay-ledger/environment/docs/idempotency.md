# Idempotency

Re-ingesting the same session directory must not duplicate executions.

Deduplicate on `(cl_ord_id, exec_id)`. A second ingest of unchanged files must print `ingested=0` on stdout and leave row counts unchanged.

Duplicate replay lines with the same `ClOrdID` and `ExecID` must be ignored, not double-counted in export.
