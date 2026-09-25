# WAL barrier — commit unlock order

Host-local index-ops WAL gate for the tantool control plane. Commit writes /app/state/wal-record.json and a fsync marker file /app/state/wal-{index}.marker containing the live doc count.

The commit lock must remain held until the WAL fsync marker is written. wal-record.json stores lock_released_before_fsync which must be false after a successful commit. stats exposes this as commit_lock_released_before_wal.
