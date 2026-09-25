# Tombstone retention window

Default retention window: 600000 ms unless TB3_TOMB_RETENTION_MS overrides.

For each partition, high_water_ms is the maximum timestamp_ms among all records on that partition.

A tombstone is eligible for lineage when timestamp_ms >= high_water_ms - retention_ms.

Expired tombstones produce tomb_expired findings during reconcile.
