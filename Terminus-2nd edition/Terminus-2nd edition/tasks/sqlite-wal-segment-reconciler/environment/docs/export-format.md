# wal-report.json export schema

Written by `wal-chain export`.

```json
{
  "applied_frame_count": 0,
  "entry_row_count": 0,
  "page_size": 4096
}
```

| Field | Meaning |
|-------|---------|
| `page_size` | WAL header page size |
| `applied_frame_count` | `SELECT COUNT(*) FROM _wal_applied` — **not** `MAX(frame_id)` |
| `entry_row_count` | `SELECT COUNT(*) FROM entries` after reconcile |

Keys are sorted. Trailing newline required.
