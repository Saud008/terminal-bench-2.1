# Level path contract

Only the following `(level, target_level)` pairs are legal reshape transitions:

- `raid1` → `raid5`
- `raid5` → `raid6`
- `raid5` → `raid1` (reshape shrink path)
- `raid10` → `raid10` (layout change at the same level)

Any array whose `(level, target_level)` pair is not in this set is blocked with reason `blocked_illegal_path`. In particular, any transition originating from or targeting `raid0` is illegal, and `raid6` → `raid5` is illegal (RAID 6 cannot be reshaped directly down to RAID 5 by this tooling).

A `level` equal to `target_level` is legal only for the `raid10` → `raid10` layout-change case listed above; no other level may transition to itself.
