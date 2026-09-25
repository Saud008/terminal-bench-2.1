# Part bundle format

Each part is a directory containing:

- `part.meta.json`
- `data.tsv` (tab-separated, header row required)

## part.meta.json

```json
{
  "part_id": "part-01",
  "batch_id": "batch-a",
  "checksum": "sha256:<hex of data.tsv bytes>",
  "min_block": 0,
  "max_block": 3,
  "table": "events"
}
```

Checksum is SHA-256 over raw `data.tsv` bytes prefixed with `sha256:`.

## data.tsv columns

| Column | Type | Meaning |
|--------|------|---------|
| `id` | string | Primary key |
| `ver` | int64 | Version column for ReplacingMergeTree-style winner |
| `value` | string | Payload |
| `expire_ts` | int64 | TTL deadline in unix milliseconds |

Parts with failing checksum must not be marked committed in SQLite (committed=0, checksum_ok=0).

When ingest or read encounters a checksum mismatch, chparts must return a non-zero exit status. Do not skip the part and continue with exit code zero.
