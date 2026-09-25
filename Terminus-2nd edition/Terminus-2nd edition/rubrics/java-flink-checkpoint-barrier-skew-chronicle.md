# Platform rubric — java-flink-checkpoint-barrier-skew-chronicle

**Task folder:** tasks/java-flink-checkpoint-barrier-skew-chronicle/

Agent maps subtasks using operator_id on each event line not modulo slotting, +3
Agent classifies UNALIGNED_DECLARED checkpoints without zeroing skew_ms, +3
Agent excludes WATERMARK events from barrier receipt counts, +3
Agent deduplicates chain-head barrier receipts credited to the next operator, +2
Agent scopes load-events idempotency keys with attempt_id, +3
Agent writes alignment.buffer JSONL with buffer_digest per contract, +2
Agent keeps emit-chronicle from mutating alignment.buffer bytes, +2
Agent sorts chronicle checkpoints and operators deterministically, +2
Agent handles TB3_FIXTURE_ROOT hidden unaligned and chained traps, +2
Agent rebuilds flink-skew.jar before verifier subprocess tests, +1
Agent does not hardcode barrier_skew_chronicle.json on disk, -3
Agent does not treat unaligned barriers as ALIGNED_OK zero skew, -3
Agent does not put bug file paths or fix order in instruction.md, -3
