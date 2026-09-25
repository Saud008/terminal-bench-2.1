# Alignment semantics

For each (checkpoint_id, attempt_id, operator_id) group:

1. Collect CHECKPOINT_BARRIER timestamps per subtask after operator mapping and watermark guard.
2. skew_ms = max(timestamp_ms) - min(timestamp_ms) across subtasks with at least one barrier.
3. alignment_class values:
   - UNALIGNED_DECLARED when any barrier row for the group has is_unaligned true
   - TIMEOUT_VIOLATION when skew_ms is strictly greater than aligned_checkpoint_timeout_ms and not unaligned
   - ALIGNED_OK when skew_ms is less than or equal to aligned_checkpoint_timeout_ms and not unaligned
   - INCOMPLETE when expected subtask count from operator graph exceeds barrier receipts

When UNALIGNED_DECLARED, skew_ms is still computed from barrier timestamps but must not be forced to zero.

aligned_checkpoint_timeout_ms defaults to 60000 when absent on events.
