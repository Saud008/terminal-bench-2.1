# Chat staging snapshot

Path: /app/state/chat-staging.json

## Top-level fields

| Field | Type | Meaning |
|-------|------|---------|
| engine | string | Always vcreplay-v1 |
| room | string | Room identifier |
| scenario | string | Scenario name |
| shard_count | int | Number of shard files read |
| event_count | int | Total events loaded |
| events | array | Normalized staged events |
| staging_digest | string | Lowercase hex SHA-256 of canonical payload |

## Staged event object

| Field | Type | Meaning |
|-------|------|---------|
| event_id | string | Unique event id |
| sender | string | Originating node id |
| type | string | message, moderation, receipt, mute_start, mute_end |
| vector_clock | object | Map node id to non-negative int |
| timestamp_ms | int | Wall clock milliseconds |
| payload | object | Type-specific body |

## staging_digest payload

Canonical JSON object hashed with keys sorted and compact separators:

```json
{
  "room": "ROOM",
  "scenario": "SCENARIO",
  "events": [ ... staged events in shard load order ... ]
}
```

staging_digest is lowercase hex SHA-256 of the canonical payload. The snapfreeze module uses crypto/sha256 in Go. Fixture builder build_fixtures.py uses hashlib with the same canonical JSON rules.
