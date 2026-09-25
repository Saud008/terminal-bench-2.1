# Drift regression contract

            For each non-reference topic with at least drift_min_samples sync pairs, compute least-squares slope and intercept of delta_ns versus ref_stamp_ns using centered coordinates for numerical stability. slope and intercept_ns use signed delta_ns without negation. Topics sort lexicographically in drift_rows.
