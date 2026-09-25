# Thermal excursion lemma

For each lot, consider telemetry rows whose lot_alias resolves to that lot_id.

A row is thermally excursive when celsius is strictly greater than threshold_celsius and minute_index is greater than or equal to excursion_limit_minutes (inclusive boundary).

excursion_minutes is the maximum minute_index among excursive rows, or zero when the set is empty.

severity equals excursion_minutes multiplied by 10 plus the truncated positive celsius excess above threshold.
