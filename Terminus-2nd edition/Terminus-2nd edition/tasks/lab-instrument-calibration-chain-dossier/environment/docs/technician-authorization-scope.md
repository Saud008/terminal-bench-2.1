# Technician authorization scope

A technician is authorized on as_of_date when both conditions hold:

1. qual_expires is greater than or equal to as_of_date using ISO date lexicographic compare.
2. instrument_id appears in scope_instruments using exact case-sensitive string match.

Missing scope coverage fails authorization even when qualifications are current.
