# Platform rubric — redis-stream-consumer-group-journal-replay

**Task folder:** tasks/redis-stream-consumer-group-journal-replay/

# Rubric 1

Agent defers pending_log rows until XACK is replayed, +3
Agent sets ack_seq to the XACK journal seq not the read seq, +3
Agent rebuilds redisctl before verifier pytest, +2
Agent materializes staging snapshot at /app/state/redis-stream-stage.json, +2
Agent edits internal/decoy instead of claim replay, -3
Agent logs pending advances on XREADGROUP only, -5
Agent skips /app/state/redis-stream-stage.json snapshot, -2

# Rubric 2

Agent uses greater-than-or-equal for XAUTOCLAIM min_idle_ms, +3
Agent resolves MKSTREAM dollar id to stream tail not 0-0, +3
Agent applies consumer-local idle from delivery timestamp, +2
Agent persists group last_id in stage JSON, +2
Agent patches export rollup for idle semantics, -3
Agent treats dollar id as literal 0-0 when entries exist, -5
Agent ignores TB3_STREAM_PREFIX stream rewrites, -2

# Rubric 3

Agent counts pel_distinct as distinct message ids, +3
Agent keeps reclaim_total stable on second export pass, +3
Agent reads persisted stage between export passes, +2
Agent writes export_pass field in stream-rollup.json, +2
Agent sums delivery_count for pel_distinct, -5
Agent double-counts reclaim_total when export_pass increments, -5
Agent writes rollup without stream_lengths map, -2
