# wal-chain CLI

All paths are absolute under `/app` unless noted.

## reconcile

```
wal-chain reconcile --db <ledger.db>
```

Ensures `_wal_applied` exists, verifies each WAL frame checksum in order, records each valid frame once, and checkpoints the database. Checksum verification must complete for a frame before it is inserted into `_wal_applied`. See `/app/docs/wal-format.md`.

## stage

```
wal-chain stage --db <ledger.db>
```

Writes `<dirname(db)>/wal.stage` JSON. Must include `page_size`, `frame_count`, `salt1`, and `salt2` from the WAL header. See `/app/docs/staging-format.md`.

## export

```
wal-chain export --db <ledger.db> --out <report.json>
```

Example: `wal-chain export --db /app/state/ledger.db --out /app/output/wal-report.json`

Requires `wal.stage` beside the database. `applied_frame_count` is the number of rows in `_wal_applied`, not the highest frame id. See `/app/docs/export-format.md`.
