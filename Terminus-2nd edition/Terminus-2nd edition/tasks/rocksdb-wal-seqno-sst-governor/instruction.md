Implement the rocksctl WAL and compaction governor on the working Rust baseline under /app. The tool ingests offline WAL batch descriptors and mock SST catalog entries from a fixture directory, writes a normalized staging snapshot at /app/state/rocksdb-stage.json, plans compaction against the seqno watermark, and exports live column-family visibility plus compaction statistics to /app/output/fab-lsm-governor.json with companion digest at /app/output/compaction-checksum.txt

Your work must satisfy every contract cited below. The src/decoy module is not on the wal ingest or compact plan export hot path and must not be edited for a correct export.

Build /app/bin/rocksctl from the workspace root. Subcommands:

  rocksctl wal ingest <fixture-dir>
  rocksctl compact plan export [--pass N]

After ingest, /app/state/rocksdb-stage.json must list wal batches in source filename order and sst files in source filename order with snapshot_seqno and watermark_seqno copied from the fixture manifest.

compact plan export reads staging only (never re-parse raw JSON from the ingest directory). It writes /app/output/fab-lsm-governor.json and derives /app/output/compaction-checksum.txt from the canonical governor JSON defined in /app/docs/export-checksum.md

Snapshot key visibility must follow /app/docs/seqno-visibility.md: only committed WAL batches with batch seqno less than or equal to snapshot_seqno contribute puts; uncommitted batches must not surface keys even when their assigned seqno is below the snapshot bound.

Compaction SST selection must follow /app/docs/compaction-watermark-planner.md: include only SST files whose max_seqno is less than or equal to watermark_seqno, ordered by file_id. Picking files by descending size_bytes without the watermark filter is incorrect.

Range tombstone masking must follow /app/docs/range-tombstone-bounds.md: a range with start and end hides keys k where start less than or equal to k and k less than end (half-open upper bound). Treating end as inclusive is incorrect.

Merge operand export must follow /app/docs/merge-operator-finalize.md: when finalized is false the export must not publish partial_value; the published value is the sum of numeric operands after finalize semantics.

Reclaimed byte accounting must follow /app/docs/reclaim-idempotency.md: reclaimed_bytes is the sum of size_bytes across selected SST on the first pass; a second export pass with --pass 2 must report the same reclaimed_bytes when staging is unchanged. Adding prior pass reclaimed totals again is incorrect.

Bundled fixtures use /app/data as the fixture directory (manifest.json plus wal/ and sst/ subdirectories). Hidden verifier fixtures may supply additional WAL and SST JSON and TB3_KEY_PREFIX key mutation at runtime.
