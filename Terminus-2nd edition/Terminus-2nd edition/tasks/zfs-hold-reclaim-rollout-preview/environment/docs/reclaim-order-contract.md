# Reclaim order contract

Eligible snapshots (those blocked by none of the gates) are ranked deterministically: sort by `depth` descending, then by `creation_txg` ascending, then by `name` ascending. `reclaim_rank` is assigned starting at 1 in that sorted order and stored on each eligible row alongside `name`, `depth`, and `creation_txg`.

When a single snapshot would be blocked by more than one gate at once, exactly one `block_reason` is recorded, using this precedence, highest first: `blocked_hold`, then `blocked_clone`, then `blocked_bookmark`, then `blocked_pool_floor`. For example a held snapshot that is also a clone origin is recorded as `blocked_hold`, not `blocked_clone`.

Re-running `compile` against the same loaded inventory must produce the same eligible ordering and the same block reasons every time; ranking must not depend on iteration order of the underlying object list.
