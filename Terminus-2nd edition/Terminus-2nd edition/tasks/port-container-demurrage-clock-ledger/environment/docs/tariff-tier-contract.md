# Tariff tier contract

Demurrage charges apply after free_days are consumed on eligible calendar days.

## Tier boundaries

Demurrage day numbering starts at one for the first billable day after free time.

| Demurrage day | Tier | Rate field |
|---------------|------|------------|
| 1 through 3 | tier1 | tier1_rate_cents |
| 4 through 7 | tier2 | tier2_rate_cents |
| 8 and above | tier3 | tier3_rate_cents |

## Carrier tariffs

Tariff rows are keyed by carrier_id. Each container uses its carrier tariff for tier rate lookup.

## Staging totals

staged_dwell stores tier1_days, tier2_days, tier3_days counts and total_cents sum per container.
