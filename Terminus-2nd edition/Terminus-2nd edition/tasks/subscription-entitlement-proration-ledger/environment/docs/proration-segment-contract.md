# proration-segment-contract.md

## Base allocation

`segment_days` = inclusive days from `window_start` through `window_end` (after anchor shift).

`base_cents = monthly_cents * segment_days // cycle_days` (integer division; `0` when `cycle_days = 0`).

## Plan-change credit (mid-cycle)

When segment index `i > 0`, subtract credit for the immediately preceding plan change:

```
credit = old_monthly_cents * inclusive_days(change_date, cycle_end) // cycle_days
base_cents = segment_base - credit
```

`old_monthly_cents` is the **from_plan** monthly rate of that change. `change_date` is inclusive through `cycle_end`.

### Invoice encoding (required)

- Fold credit into the **new** segment’s `base_cents` (may be negative before overage/coupons; typically non-negative after credit).
- **`proration_cents` is always `0`** on published invoice lines.
- Do **not** emit a separate negative invoice row or standalone credit line for the old plan.

### Worked example — `mid-upgrade`

Cycle `2026-02-01` … `2026-02-28` (28 days). Change `2026-02-15` starter→growth (2800→5600 cents).

| segment | window | days | raw base | credit | final base_cents |
| --- | --- | ---: | ---: | ---: | ---: |
| 0 starter | Feb 1–14 | 14 | 1400 | — | 1400 |
| 1 growth | Feb 15–28 | 14 | 2800 | 1400 | 1400 |

Credit = `2800 * 14 // 28 = 1400`. Both invoice lines carry `proration_cents: 0`.

### Same-day change at cycle start

When `event_date == cycle_start`, the prior segment has `segment_days = 0` and `base_cents = 0`. The new segment spans the full remaining cycle; credit uses all remaining inclusive days through `cycle_end`.

Example: cycle `2026-11-01` … `2026-11-30`, change on Nov 1 starter→growth (3000→6000):

- segment 0: `base_cents = 0`
- segment 1: raw `6000`, credit `3000`, final `base_cents = 3000`, `proration_cents = 0`
