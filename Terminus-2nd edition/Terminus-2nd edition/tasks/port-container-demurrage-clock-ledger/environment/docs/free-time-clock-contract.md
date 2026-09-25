# Free time clock contract

Eligible dwell days are calendar days inside the gate window that are not closure days and not hold-paused days.

## Free day consumption

Contracted free_days from the container contract consume eligible days first in calendar order. Remaining eligible days after free consumption become demurrage days numbered from one.

## Eligible day rules

Closure days are excluded entirely. They do not consume free time and do not accrue demurrage. Hold-covered days pause the clock and are not eligible.

## Outputs

run-dwell-ledger writes eligible_days, free_days_used, and demurrage_days per container into staged_dwell.
