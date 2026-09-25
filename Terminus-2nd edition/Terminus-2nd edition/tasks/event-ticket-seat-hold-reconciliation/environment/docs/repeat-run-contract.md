# Idempotency contract

run_stamp is first 16 hex chars of sha256(hold_snapshot_digest + "|" + scenario name).

Identical hold snapshot and scenario produce identical run_stamp and assignment sequence.
