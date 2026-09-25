# Post-reconcile invariants

After a successful `wal-chain reconcile` followed by `stage` and `export` on database `D` with WAL `D-wal`:

1. `SELECT COUNT(*) FROM _wal_applied` equals the number of valid WAL frames in `D-wal` when parsed with page size from header offset 8.
2. `SELECT COUNT(DISTINCT frame_id) FROM _wal_applied` equals `SELECT COUNT(*) FROM _wal_applied` (no duplicate frame ids).
3. Running `wal-chain reconcile --db D` a second time does not increase `_wal_applied` row count.
4. `wal.stage` contains `salt1` and `salt2` matching WAL header bytes 16–23.
5. `wal-report.json` field `applied_frame_count` equals invariant (1), not the highest frame id when some frames were skipped.
6. `entry_row_count` in the report matches `SELECT COUNT(*) FROM entries`.
7. If a frame checksum is invalid, reconcile exits non-zero and does not insert that frame into `_wal_applied`.
8. Additional verifier fixture databases under `/opt/verifier-fixtures/wal/hidden` (TB3_HIDDEN) must reconcile with the same invariants as bundled seed data.

Operators may query these invariants directly with `sqlite3`.
