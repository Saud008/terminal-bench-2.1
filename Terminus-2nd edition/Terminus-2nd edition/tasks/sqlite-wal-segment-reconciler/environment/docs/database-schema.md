# Ledger database schema

The reconciler operates on SQLite databases that contain business rows and a WAL application ledger.

## `entries`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `sku` | TEXT NOT NULL | Stock-keeping unit label |
| `qty` | INTEGER NOT NULL | Quantity on hand |

`entry_row_count` in export reports is `SELECT COUNT(*) FROM entries`.

## `_wal_applied`

Created by `wal-chain reconcile` when missing. Records which WAL frames were applied.

| Column | Type | Notes |
|--------|------|-------|
| `rowid` | INTEGER PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `frame_id` | INTEGER NOT NULL | 1-based WAL frame index |
| `page_no` | INTEGER NOT NULL | Page number from the frame header |
| `applied_at` | TEXT NOT NULL | UTC timestamp default `strftime('%Y-%m-%dT%H:%M:%fZ','now')` |

`applied_frame_count` in export reports is `SELECT COUNT(*) FROM _wal_applied`, not `MAX(frame_id)`.

Reconcile must verify each frame checksum before inserting a row. A second reconcile must not increase row count when frames are unchanged.
