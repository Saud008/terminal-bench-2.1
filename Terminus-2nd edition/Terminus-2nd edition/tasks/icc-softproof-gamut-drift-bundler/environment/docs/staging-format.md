# Staging format

Path: dirname(readings)/icc.stage.json

Schema: icc-softproof-stage/1

| Field | Type | Description |
|-------|------|-------------|
| schema | string | Always icc-softproof-stage/1 |
| readings_digest | string | sha256 hex of readings file bytes |
| profile_digest | string | sha256 hex of profile file bytes |
| paper_digest | string | sha256 hex of paper file bytes |
| profile_id | string | From profile JSON |
| patches | array | Normalized patch rows |
| evaluation | object or null | Filled by evaluate |

Each patch row: patch_id, L, a, b, batch_id

evaluation object after evaluate:

| Field | Type |
|-------|------|
| policy_digest | string |
| evaluated_as_of | integer epoch |
| profile_checksum_ok | boolean |
| per_patch | array of evaluated patch rows |

per_patch rows sorted by patch_id ascending.
