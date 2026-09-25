# Holiday rollup contract

Billing days for invoice-rollup.json equal inclusive calendar days from period_start through period_end minus holidays listed in the scenario holidays array.

Count every date d where period_start <= d <= period_end, then subtract one for each holiday date that falls inside that inclusive range.

Holidays outside the billing period do not affect billing_days.

Example: period 2026-01-01 through 2026-01-07 with holidays [2026-01-01, 2026-01-20] yields 7 minus 1 equals 6 billing days.

invoice-rollup.json field billing_days uses this count before publish-invoice.
