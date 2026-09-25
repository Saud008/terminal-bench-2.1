Implement the WAL segment reconciler at /app/bin/wal-chain: a three-stage workflow that applies sidecar WAL frames into a ledger SQLite database, writes a staging snapshot beside the database, and exports a frame report JSON. Wire reconcile, stage, and export to match /app/docs/wal-format.md, /app/docs/staging-format.md, /app/docs/export-format.md, /app/docs/invariants.md, and /app/docs/cli.md.

For any --db path, the staging snapshot path is always dirname(db)/wal.stage. Example: --db /app/state/ledger.db writes /app/state/wal.stage; --db /tmp/work/ledger.db writes /tmp/work/wal.stage. Export requires that wal.stage file beside the database.

WAL header rules: page size is the big-endian uint32 at byte offset 8 in the db-wal sidecar. Frame count is (file_size - 32) / (24 + page_size). Salt-1 and salt-2 are at offsets 16 and 20. Reconcile must verify each frame CRC32 rolling checksum before inserting that frame into _wal_applied; invalid checksum aborts reconcile with non-zero exit and must not insert that frame.

Staging snapshot wal.stage is compact JSON with sorted keys and a trailing newline. Required fields: page_size (from WAL offset 8), frame_count, salt1, salt2 (from WAL offsets 16 and 20). Export refuses to run without wal.stage present.

Reconcile idempotency: running wal-chain reconcile --db D a second time must not increase SELECT COUNT(*) FROM _wal_applied.

Export report fields: applied_frame_count is SELECT COUNT(*) FROM _wal_applied, not MAX(frame_id) and not the WAL header frame count. entry_row_count is SELECT COUNT(*) FROM entries. page_size is the WAL header page size. JSON keys are sorted with compact separators and a trailing newline.

Example workflow:

/app/bin/wal-chain reconcile --db /app/state/ledger.db
/app/bin/wal-chain stage --db /app/state/ledger.db
/app/bin/wal-chain export --db /app/state/ledger.db --out /app/output/wal-report.json
