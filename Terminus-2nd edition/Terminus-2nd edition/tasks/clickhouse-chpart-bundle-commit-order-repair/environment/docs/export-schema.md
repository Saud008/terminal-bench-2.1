# Export schema

/app/output/parts-report.json:

```json
{
  "table_name": "TB3_<suffix>_events",
  "max_block_number": 0,
  "row_count": 0,
  "rows": [
    {"id": "<pk>", "ver": 0, "value": "<string>", "expire_ts": 0}
  ],
  "parts": [
    {"part_id": "<id>", "row_count": 0, "checksum_ok": true, "committed": true}
  ]
}
```

- table_name matches the staged snapshot table_name.
- max_block_number mirrors the snapshot max_block_number after the commit barrier.
- rows sorted ascending by id.
- parts sorted ascending by part_id.
- row_count equals len(rows).
- Values must match the staged snapshot at /app/state/parts-snapshot.json, not SQLite re-query or /app/state/parts.manifest.

Idempotent re-ingest of the same part bundle must not duplicate merged rows or inflate row_count.
