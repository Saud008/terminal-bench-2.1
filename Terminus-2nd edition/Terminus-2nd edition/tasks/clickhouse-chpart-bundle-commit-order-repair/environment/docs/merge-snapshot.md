# Merge snapshot

Ingest writes /app/state/parts-snapshot.json after merge, TTL pruning, and commit barrier finalize.

## Schema

```json
{
  "table_suffix": "<suffix>",
  "table_name": "TB3_<suffix>_events",
  "max_block_number": 0,
  "fsynced": false,
  "parts": [
    {"part_id": "<id>", "row_count": 0, "checksum_ok": true, "committed": true}
  ],
  "rows": [
    {"id": "<pk>", "ver": 0, "value": "<string>", "expire_ts": 0}
  ],
  "idempotency_key": ""
}
```

- table_suffix mirrors CHPARTS_TABLE_SUFFIX (default default).
- table_name is TB3_<suffix>_events.
- rows are merged by primary key keeping the row with the maximum ver.
- max_block_number is the highest max_block among ingested parts after fsynced is true.
- Before walking parts, ingest calls staging.WriteEarlyManifest to create /app/state/parts.manifest with empty rows. Export must not read it; export reads parts-snapshot.json only.
- /app/state/parts.manifest is a legacy scratch file written at ingest start with rows empty; export must not read it.

Export reads this snapshot only.
