# Detached part handling

When any metadata row for a partition_id has detached true, the partition readiness_state must be detached.

Detached partitions are excluded from ready counts in totals.ready_count.
