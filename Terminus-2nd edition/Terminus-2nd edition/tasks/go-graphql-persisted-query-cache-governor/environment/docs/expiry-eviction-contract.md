# Expiry eviction contract

ttl_ms is expiry.json ttl_ms plus TB3_TTL_BIAS (floored at zero).

A row with status active is evicted when:

now_ms - last_seen_ms > ttl_ms

Use last_seen_ms as the TTL anchor. Do not use registered_at_ms for expiry age.

Eviction sets status to evicted without deleting the row.

Reconcile applies expiry before quota enforcement.

PQGOV_NOW_MS overrides reconcile clock when set.
