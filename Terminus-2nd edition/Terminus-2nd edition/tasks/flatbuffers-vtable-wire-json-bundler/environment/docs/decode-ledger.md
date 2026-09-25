# Decode ledger

Path: `/app/state/decode.ledger.jsonl`

## Artifact paths

| Path | Role |
|------|------|
| `/app/state/decode.snapshot.json` | Staging envelope written by `stage`, read by `export` |
| `/app/state/decode.ledger.jsonl` | Append-only ledger written by `stage`, read by `export` |

## Ledger record (one JSON object per line)

| Field | Type | Description |
|-------|------|-------------|
| `seq` | integer | Monotonic line number starting at 1 |
| `hn55` | string | Same value as staging envelope `hn55` |
| `export_digest` | string | 16 lowercase hex digits hashing the staged `scene` object |
| `revision` | integer | Scene revision at stage time |

## Head binding

Export binds to the latest ledger record and the staging envelope written for that record. `hn55`, `revision`, and `export_digest` on the ledger head must match the reloaded staging envelope.
