# Settlement staging and export

## Staging snapshot

Ingest writes /app/state/settlement-staging.json containing:

| Field | Meaning |
|-------|---------|
| events | validated event objects in processing order |
| events_digest | SHA-256 hex of canonical event bodies joined by newline |
| season_id | season_id from ingest --season |
| pool_epoch | pool_epoch from that season |
| staging_generation | monotonic ingest counter persisted in /app/state/staging-seq.json |

Digest ordering: sort events by (timestamp_ms, seq, event_id) ascending, strip signature from each body, canonical JSON per event-envelope.md, concatenate with newline separators, hash UTF-8 bytes.

## Settle persistence

Settle bumps /app/state/replay-generation.json generation counter by 1 and writes /app/state/pity-ledger.json with per-player inventory, shards, pity_legendary, season_id.

## Export gate

Export reads staging and replay-generation. It must verify events_digest matches recomputation from staging events and that export uses the current generation value written by the last settle.

Export writes /app/output/settlement-report.json with players map, audit_log sorted by (timestamp_ms, seq, event_id), and settlement_digest.

## Canonical report JSON

Canonical JSON for digests and sealed bytes means:

1. Object keys sorted lexicographically at every nesting depth (recursively), not only at the top level.
2. Compact serialization: separators are comma and colon with no extra whitespace and no pretty printing.
3. Arrays keep element order; nested objects inside arrays are still key-sorted recursively.

Sorting only top-level keys is not sufficient; nested maps such as players and inventory entries must also use recursively sorted keys so the hashed byte sequence is fully determined.

## settlement_digest

settlement_digest is the lowercase hex SHA-256 of the canonical JSON encoding of the report object after the settlement_digest key is removed entirely from that object.

Do not retain settlement_digest with an empty string (or any other placeholder value) in the hashed payload. The key must be absent before serialization and hashing. After the digest is computed, write settlement_digest into the sealed report file as the resulting hex string.

Export must not re-settle events; it serializes ledger state produced by settle.
