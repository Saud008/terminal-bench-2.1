# Stay calculation contract

Each entry stamp contributes inclusive day counts from entry_date through exit_date. When exit_date is empty the open visit runs through reference_date inclusive.

cumulative_stay_days sums all stamp segments for the passport. remaining_stay_days = max(0, max_stay_allowed - cumulative_stay_days).

Deny when cumulative_stay_days > max_stay_allowed + grace_days. grace_days comes from the scenario manifest.
