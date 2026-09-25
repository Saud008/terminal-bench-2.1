# Binlog checkpoint

Each insert enqueues a row in binlog_pending with committed=0.

On rotate, checkpoint_after_rotate must:

1. Commit every pending binlog row (set committed=1) before writing binlog-checkpoint.json.
2. Never delete uncommitted pending rows during rotate.
3. Set last_committed_seq to the maximum seq in binlog_pending after commit.
4. Set rotate_seq to the rotate-meta rotate_seq value for this rotate.

Search and disk chunks must reflect all inserts from batches indexed before rotate completes.
