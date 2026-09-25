# anchor-shift-contract.md

After segment boundaries are computed, truncate `window_end` using `anchor_shifts` (sorted by `effective_date` ascending).

Skip a shift when `effective_date` is **after** the segment’s pre-shift `window_end`.

For each remaining shift:

1. Parse `effective_date` as `(y, m, _)`.
2. `anchor_day = min(new_anchor_day, 28)`.
3. `candidate = date(y, m, anchor_day)`.
4. While `candidate < effective_date`, advance one calendar month (December → January of next year) and rebuild `candidate` with the same `anchor_day` rule.
5. If `candidate <= current window_end` **and** `candidate <= cycle_end`, set `window_end = candidate`.

Recompute `segment_days` and `base_cents` from the truncated window.

### Worked example — `anchor-shift`

Cycle `2026-07-01` … `2026-07-31` (31 days), single starter segment, shift effective `2026-07-10`, `new_anchor_day = 15`:

- pre-shift window: Jul 1–Jul 31
- candidate: Jul 15 (≥ Jul 10, ≤ Jul 31) → truncated `window_end = 2026-07-15`
- `segment_days = 15`, `base_cents = 3100 * 15 // 31 = 1500`
