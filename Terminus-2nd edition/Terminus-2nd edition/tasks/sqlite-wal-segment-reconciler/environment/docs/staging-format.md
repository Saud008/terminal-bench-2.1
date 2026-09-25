# wal.stage staging snapshot

Path: `<database_directory>/wal.stage` (for `/app/state/ledger.db` → `/app/state/wal.stage`).

JSON object, UTF-8, sorted keys, compact separators `,` and `:`, trailing newline required.

Required fields:

| Field | Type | Source |
|-------|------|--------|
| `page_size` | integer | WAL header offset 8 |
| `frame_count` | integer | derived frame count |
| `salt1` | integer | WAL header offset 16 |
| `salt2` | integer | WAL header offset 20 |

Export refuses to run without both salt fields present.
