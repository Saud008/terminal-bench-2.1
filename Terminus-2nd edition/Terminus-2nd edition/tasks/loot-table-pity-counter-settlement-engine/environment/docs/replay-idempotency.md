# Processed-event idempotency

Settle maintains /app/state/processed-events.json listing event_id values already applied. If settle encounters an event_id already recorded, skip all inventory, shard, and pity mutations for that event and append an audit entry with action duplicate_skip.

Idempotency is keyed only on event_id. Re-running settle on the same staging without clearing processed-events must not double-credit players.
