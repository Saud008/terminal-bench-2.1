# Dedup ledger

Replay must skip duplicate `signal_id` values after the first acceptance. Increment `dedup_skipped` for each duplicate attempt.

Do not append duplicate ids to `dedup_seen`.
