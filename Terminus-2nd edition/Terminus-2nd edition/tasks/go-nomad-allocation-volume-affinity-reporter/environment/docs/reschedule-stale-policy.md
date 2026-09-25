# Reschedule stale policy

Reschedule total sums reschedule_attempts only when reschedule_failed is true and attempts is greater than zero.

Stale suppression drops allocations with non-empty superseded_by or modify_index strictly below stale_cutoff_index from the placement buffer.

Apply drain eligibility before stale filtering.
