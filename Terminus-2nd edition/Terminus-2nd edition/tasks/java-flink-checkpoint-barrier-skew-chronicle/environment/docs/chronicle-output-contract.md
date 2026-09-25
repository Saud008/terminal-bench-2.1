# Chronicle output contract

barrier_skew_chronicle.json top-level fields:

| Field | Type | Notes |
|-------|------|-------|
| job_id | string | From fixtures/config/job_meta.json |
| alignment_timeout_ms | int | Policy default |
| checkpoints | array | Sorted by checkpoint_id then attempt_id |

Each checkpoint object contains operators array sorted by operator_id ascending. Each operator row copies skew_ms, alignment_class, barriers_received, expected_subtasks from alignment buffer and adds misalignment_class:

- misalignment_class mirrors alignment_class except TIMEOUT_VIOLATION becomes SKEW_TIMEOUT when skew_ms exceeds timeout.

summary block per checkpoint: operator_count, max_skew_ms, timeout_violation_count, unaligned_count.
