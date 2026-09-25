Staging snapshot

Written to /app/state/rekey-snapshot.json and mirrored to /app/state/rekey.manifest. Fields:

snapshot_version — always 1
table_suffix — from VERIFIER_TABLE_SUFFIX or default
trace_id — trace basename
initiator_offset — from VERIFIER_INITIATOR_OFFSET or 0
verdicts — per-event records with order_ok, selectors_ok, uid_ok, seq_monotonic, accepted, reject_reason, active_spi_out
active_spi_out — SPI_OUT of the single active non-deleted CHILD_SA at end of replay
rekey_violation_count — count of verdicts with accepted false and reject_reason in rekey_before_delete_ack, selector_narrowed, uid_reused, seq_not_monotonic
