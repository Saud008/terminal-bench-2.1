# Ledger schema contract

Compile writes `/app/state/reclaim-ledger.json` with:

- `run_id` (string)
- `scenario` (string)
- `load_seq` (integer)
- `pool` (string)
- `free_pct` (number)
- `floor_pct` (number)
- `eligible` (array of `{name, depth, creation_txg, reclaim_rank}`)
- `blocked` (array of `{name, block_reason}`)
- `eligible_count` (integer)
- `blocked_count` (integer)

## block_reason priority

When multiple gates would block the same snapshot, record a single `block_reason` using this priority order:

1. `blocked_hold`
2. `blocked_clone`
3. `blocked_bookmark`
4. `blocked_pool_floor`

Pool floor, when active, applies to all snapshots; combine with the priority above so a held snapshot under a failed floor still reports `blocked_hold`.
