# Pool epoch binding

Each season config declares pool_epoch. Events must carry the same pool_epoch as their season config at settlement time.

Reject events where event.pool_epoch does not equal season.pool_epoch for the resolved season file. Staging records the primary season pool_epoch from the ingest --season argument; settlement still validates every event against its own season config.

Pool epoch mismatch is a hard error during settle, not a silent skip.
