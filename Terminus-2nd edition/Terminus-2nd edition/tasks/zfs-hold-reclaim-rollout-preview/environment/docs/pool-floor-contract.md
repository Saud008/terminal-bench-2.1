# Pool floor contract

A reclaim rollout preview only proceeds when the pool's free space is strictly above its configured floor: `free_pct` must be strictly greater than `floor_pct`.

When `free_pct` is not strictly greater than `floor_pct` (that is, `free_pct < floor_pct` or `free_pct == floor_pct`), every snapshot in the inventory is blocked with reason `blocked_pool_floor`, even snapshots that carry no holds, are not clone origins, and are not bookmark targets. Equal free and floor percentages are not sufficient headroom for a rollout.

This gate is evaluated per snapshot alongside the hold, clone, and bookmark gates; see reclaim-order-contract.md for how block reasons combine when more than one gate would block the same snapshot.
