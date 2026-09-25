Event sequence policy

log_seq must strictly increase on every event line in the trace. Rekey boundaries do not reset or relax monotonicity. Equal or decreasing log_seq sets seq_monotonic false, reject_reason seq_not_monotonic.
