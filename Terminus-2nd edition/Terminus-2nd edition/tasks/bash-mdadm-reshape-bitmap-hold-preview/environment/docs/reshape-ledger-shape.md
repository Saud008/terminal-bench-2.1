# Ledger schema contract

Compile writes `/app/state/reshape-ledger.json` with:

- `run_id` (string)
- `scenario` (string)
- `load_seq` (integer)
- `fleet` (string)
- `window_hours` (number)
- `eligible` (array of `{name, salted_name, criticality, level, target_level}`, sorted per eligibility-rank-rules.md)
- `blocked` (array of `{name, block_reason}`, sorted by `name` ascending)
- `eligible_count` (integer)
- `blocked_count` (integer)

## block_reason priority

When multiple gates would block the same array, record a single `block_reason` using this priority order:

1. `blocked_bitmap`
2. `blocked_spare_hold`
3. `blocked_degraded`
4. `blocked_illegal_path`
5. `blocked_window`
