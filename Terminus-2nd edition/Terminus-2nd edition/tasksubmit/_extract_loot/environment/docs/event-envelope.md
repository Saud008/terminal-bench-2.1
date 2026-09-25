# Event envelope and HMAC signature

Each loot pull event is a JSON object ingested from JSONL streams. Required fields: event_id, player_id, season_id, pool_epoch, event_type, item_id, rarity, seq, timestamp_ms, nonce, signature.

Canonical signing body excludes the signature field entirely (the key must be absent, not present with an empty value). Serialize as compact JSON with recursively sorted object keys at every nesting depth and separators (comma, colon) with no extra whitespace. Top-level-only key sorting does not define the required bytes when nested objects appear.

HMAC-SHA256 key material is the string `{hmac_secret}:{pool_epoch}` where hmac_secret comes from the season config matching season_id.

Reject events whose recomputed signature does not match the signature field. Ingest must not write unsigned or invalid events into staging.
