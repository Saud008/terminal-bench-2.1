# Parity report schema

export report writes JSON with seed, scenario, run_id, parity_ok, summary object, and audit_digest.

summary contains mismatch_count, ttl_filtered_count, duplicate_ts_resolved, and as_of_ts list sorted ascending.

audit_digest is lowercase hex SHA-256 of canonical JSON for the summary object only with sorted keys at every object depth and no insignificant whitespace.

Parity row detail remains in /app/work/parity.db parity_rows for the run_id.
