# Retention bucket rules

Policy fields:

| Field | Meaning |
|-------|---------|
| keep_daily | Number of calendar days ending at reference_now date (inclusive) |
| keep_weekly | Number of week buckets ending at the week containing reference_now |
| keep_monthly | Number of calendar months ending at reference_now month |
| keep_yearly | Number of calendar years ending at reference_now year |
| week_start | monday or sunday — first day of weekly bucket |
| clock_skew_sec | Seconds ahead of reference_now before timestamp clamp |

For each bucket horizon, select the listed number of most-recent bucket keys relative to reference_now. Within each selected bucket, keep the archive whose **normalized** timestamp is latest; ties break on higher source line number.

The union of all bucket survivors and legal holds forms kept archives. All other parsed archives are pruned.
