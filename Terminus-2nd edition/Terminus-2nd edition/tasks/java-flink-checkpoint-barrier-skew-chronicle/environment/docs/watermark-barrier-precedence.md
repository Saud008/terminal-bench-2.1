# Watermark vs barrier precedence

WATERMARK events must never increment barrier receipt counts or substitute for CHECKPOINT_BARRIER timestamps.

When a WATERMARK shares the same subtask_index and operator_id as a pending barrier group, the watermark is recorded for precedence audit only and excluded from skew min/max math.

CHECKPOINT_COMPLETED events are informational and do not count toward barrier receipts.
