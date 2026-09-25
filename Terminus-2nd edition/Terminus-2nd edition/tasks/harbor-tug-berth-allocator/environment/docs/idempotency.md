# Replay and idempotency

Harbor dispatch feeds may replay the same voyage segment after a partial outage. ingest must treat voyage_id as part of the idempotency key together with berth_id and arrival_utc.

Replays that only differ by departure_utc still collide when voyage_id, berth_id, and arrival_utc match.

Stats must remain consistent with SQLite transaction boundaries.
