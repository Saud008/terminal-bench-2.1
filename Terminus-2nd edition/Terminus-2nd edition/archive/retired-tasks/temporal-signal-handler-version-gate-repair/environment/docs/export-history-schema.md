# Export history schema

Output path example: `/app/output/signal-history-export.json`

```json
{
  "workflow_id": "string",
  "effective_version": "semver",
  "history_events": [
    {"signal_id": "string", "name": "string", "version": "semver", "offset_ms": 0}
  ],
  "duplicate_skipped": 0,
  "heartbeat_clock_source": "server",
  "heartbeat_offsets_ms": [0]
}
```

`history_events` includes **all** accepted signals, including those with `target_version` below `migration_version`. Export must not truncate pre-migration events.

`history_events` preserve acknowledgement delivery order from staging (`acked_signals` order). Do not reorder rows by `signal_id`.

`duplicate_skipped` equals staging `dedup_skipped`.
