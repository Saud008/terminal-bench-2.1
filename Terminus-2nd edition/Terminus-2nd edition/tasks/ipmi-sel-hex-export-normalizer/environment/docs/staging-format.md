# SEL ingest staging snapshot

Path: /app/state/sel.stage adjacent to the database directory.

Written after each successful ingest invocation. JSON object with sorted keys, compact separators, trailing newline.

| Field | Type | Meaning |
|-------|------|---------|
| accepted | integer | Rows newly inserted this run |
| rejected_checksum | integer | Records failing record_xor this run |
| duplicate_rejected | integer | Records skipped because record_id already exists |
| ingest_digest | string | Lowercase hex SHA-256 of the raw input blob bytes |

Counts reflect only the current ingest call, not lifetime totals.
