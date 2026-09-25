# Platform rubric — sqlite-wal-segment-reconciler

**Task folder:** tasks/sqlite-wal-segment-reconciler/

Agent implements wal-chain reconcile that verifies WAL frame CRC32 checksums before inserting into _wal_applied, +3
Agent restores db-wal from wal.snap sidecar when the live sidecar file is missing during reconcile, +2
Agent writes wal.stage beside the database with page_size frame_count salt1 and salt2 from WAL header bytes, +3
Agent terminates wal.stage JSON with a trailing newline after compact sorted keys, +1
Agent makes second reconcile idempotent so _wal_applied row count does not grow, +2
Agent exports applied_frame_count as SELECT COUNT from _wal_applied not MAX frame_id, +3
Agent requires wal.stage present before export and copies page_size from staging snapshot, +2
Agent aborts reconcile with non-zero exit when a frame checksum fails without inserting that frame, +2
Agent writes export report as sorted compact JSON with trailing newline, +1
Agent patches only export.sh while leaving reconcile checksum verification broken, -3
Agent hard-codes wal.stage salt or page_size constants instead of reading the WAL sidecar header, -3
Agent uses legacy_checksum decoy path for staging or export hot path, -2
Agent drops hidden verifier fixture reconcile coverage for independent WAL pairs, -2
Agent weakens idempotency so duplicate reconcile inserts duplicate frame_id rows, -3
