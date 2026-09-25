# Replica lag suppression

lag_policy.json provides max_lag_sec threshold.

For each partition_id, compute replica_lag_max as the maximum lag_sec across all replica log rows for that partition.

When replica_lag_max is **strictly greater than** max_lag_sec, readiness_state must be suppressed regardless of mutation version.

When replica_lag_max equals max_lag_sec exactly, readiness is **not** suppressed.
