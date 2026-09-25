# Platform rubric — rocksdb-wal-seqno-sst-governor

**Task folder:** tasks/rocksdb-wal-seqno-sst-governor/

Agent filters WAL batches by committed flag before snapshot key visibility, +3
Agent selects SST files with max_seqno at or below watermark_seqno sorted by file_id, +3
Agent applies half-open range tombstone intervals with exclusive upper bound, +3
Agent sums merge operands instead of exporting partial_value when finalized is false, +3
Agent keeps reclaimed_bytes stable on compact plan export pass two without double counting, +3
Agent reads /app/state/rocksdb-stage.json in compact export instead of re-parsing fixture dirs, +2
Agent rebuilds rocksctl with cargo in test.sh after editing wal or compaction modules, +2
Agent applies TB3_KEY_PREFIX before visibility and tombstone key comparisons, +3
Agent leaves src/decoy off the wal ingest and compact export hot path, +1
Agent includes uncommitted WAL batch keys when seqno is below snapshot_seqno, -3
Agent picks SST catalog entries by descending size_bytes without watermark filter, -3
Agent treats range tombstone end key as inclusive so boundary keys disappear, -3
Agent publishes merge partial_value before operand finalize semantics, -3
Agent adds prior pass reclaimed_bytes again on the second compaction export, -3
