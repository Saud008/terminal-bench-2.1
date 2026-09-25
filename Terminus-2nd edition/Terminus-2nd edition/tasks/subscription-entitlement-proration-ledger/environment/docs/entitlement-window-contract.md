# entitlement-window-contract.md

Inclusive day count between two ISO dates: `(end - start).days + 1`. If `end < start`, the count is `0`.

`cycle_days` = inclusive days from `cycle_start` through `cycle_end`.

## Segment boundaries

Split the billing cycle at each `plan_change.event_date` (sorted ascending):

1. Build bounds: `[cycle_start, change_date_1, …, change_date_n, cycle_end]`.
2. Segment `i` uses plan `initial_plan` when `i = 0`, otherwise the `to_plan` of change `i`.
3. `window_start` = bounds[i].
4. `window_end`:
   - if another plan follows (`i < n`): the calendar day **before** the next change date (`next_change_date - 1 day`);
   - else: `cycle_end`.
5. Apply anchor-shift truncation (see `anchor-shift-contract.md`) to `window_end` before computing `segment_days` and `base_cents`.

Each segment still emits one invoice line even when `segment_days = 0` (same-day change at cycle start).
