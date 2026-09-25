# alignment.buffer format

JSONL with one object per line. Lines sorted by checkpoint_id, attempt_id, operator_id ascending.

| Field | Type | Notes |
|-------|------|-------|
| checkpoint_id | int | |
| attempt_id | int | |
| operator_id | string | Mapped operator vertex |
| skew_ms | int | Max minus min barrier timestamp delta |
| alignment_class | string | From alignment-semantics.md |
| barriers_received | int | Distinct subtasks with barriers after guards |
| expected_subtasks | int | From operator graph parallelism |
| first_barrier_ms | long | Minimum barrier timestamp |
| last_barrier_ms | long | Maximum barrier timestamp |
| buffer_digest | string | First 16 hex chars of SHA-256 over stable line body |

Stable line body excludes buffer_digest field, uses sorted JSON keys, no whitespace.
