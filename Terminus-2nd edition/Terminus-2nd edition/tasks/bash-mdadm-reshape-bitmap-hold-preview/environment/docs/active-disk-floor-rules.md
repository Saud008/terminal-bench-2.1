# Degraded floor contract

Every RAID level has a minimum number of active disks below which the array is considered degraded and unsafe to reshape. Minimums are keyed by the array's current `level` (not its `target_level`):

| level  | minimum active_disks |
|--------|-----------------------|
| raid1  | 1                     |
| raid5  | 3                     |
| raid6  | 4                     |
| raid10 | 2                     |

If an array's `active_disks` is strictly less than the minimum for its current `level`, the array is blocked with reason `blocked_degraded`.

An array whose `active_disks` equals the minimum is not degraded and is not blocked by this gate.
