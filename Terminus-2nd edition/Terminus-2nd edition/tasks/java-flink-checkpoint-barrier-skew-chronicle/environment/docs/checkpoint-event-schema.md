# Checkpoint event JSONL schema

Files use extension .jsonl under the input directory. One JSON object per line.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| event_kind | string | yes | CHECKPOINT_BARRIER, WATERMARK, CHECKPOINT_COMPLETED |
| checkpoint_id | int | yes | Checkpoint identifier |
| attempt_id | int | yes | Attempt within checkpoint (starts at 1) |
| operator_id | string | yes | Logical operator id from JobManager |
| subtask_index | int | yes | Subtask index within operator |
| timestamp_ms | long | yes | Event time in epoch milliseconds |
| is_unaligned | bool | no | True when checkpoint used unaligned barriers |
| aligned_checkpoint_timeout_ms | int | no | Alignment timeout from job config |

Lines sorted by timestamp_ms ascending after load. Tie-break by lexicographic operator_id then subtask_index ascending.
