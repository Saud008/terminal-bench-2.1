# Replay idempotency

Repeated twctl ingest calls against the same bundle directory merge witness rows by witness_id.

When an incoming witness_id already exists in staging, keep the existing row and do not append a duplicate.

ingest_seq still increments on every ingest call.

verify-result replay_deduped records how many duplicate witness ids were skipped during the latest ingest merge.
