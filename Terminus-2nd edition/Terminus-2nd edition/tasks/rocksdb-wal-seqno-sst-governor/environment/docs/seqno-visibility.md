# Seqno visibility

Snapshot reads use snapshot_seqno from staging.

WAL puts and point tombstones are visible only when the parent batch is committed and batch seqno is less than or equal to snapshot_seqno.

Uncommitted batches assign a seqno but their keys must not appear in visible_keys even when seqno is below the snapshot bound.

SST keys contribute when the parent file is selected by the compaction planner.

Latest seqno per key within a column family wins after tombstone masking.
