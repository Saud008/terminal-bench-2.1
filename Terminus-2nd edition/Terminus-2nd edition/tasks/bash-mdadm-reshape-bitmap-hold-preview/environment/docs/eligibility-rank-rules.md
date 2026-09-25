# Reshape order contract

Eligible arrays (those blocked by none of the gates) are ranked deterministically: sort by `criticality` ascending, then by `name` ascending (lexicographic). Each eligible row in the ledger and atlas carries `name`, `salted_name`, `criticality`, `level`, and `target_level`, in that sorted order.

When a single array would be blocked by more than one gate at once, exactly one `block_reason` is recorded, using this precedence, highest first: `blocked_bitmap`, then `blocked_spare_hold`, then `blocked_degraded`, then `blocked_illegal_path`, then `blocked_window`. For example an array with a frozen internal bitmap that is also outside the window-hour budget is recorded as `blocked_bitmap`, not `blocked_window`.

Re-running `compile` against the same scanned inventory must produce the same eligible rank and the same block reasons every time; ranking must not depend on iteration order of the underlying array list.
