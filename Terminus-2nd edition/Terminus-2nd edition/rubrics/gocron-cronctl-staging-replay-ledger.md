# Platform rubric — gocron-cronctl-staging-replay-ledger

**Task folder:** tasks/gocron-cronctl-staging-replay-ledger/

Agent writes replay-snapshot.json with planned_fires sorted by at_ms then job_id, +3
Agent computes fires_digest from canonical fire ordering per snapshot-contract.md, +3
Agent increments replay-generation.json on each replay run, +2
Agent respects TB3_CLOCK_START and TB3_TICK_MS controllable clock overrides, +3
Agent applies planned fires inside each tick window for arbitrary TB3_TICK_MS, +2
Agent suppresses DST spring-gap fires per dst-gap-handling.md, +3
Agent coalesces singleton overlap entries without double execution, +3
Agent gates leases independently per job id, +2
Agent persists execution rows to SQLite ledger.db after replay, +2
Agent exports ledger JSON combining staging snapshot with ledger rows, +3
Agent rejects export when generation gate or digest mismatch, +3
Agent applies job location timezone rules not only TZ tag, +2
Agent releases distributed lock after panic recovery, +2
Agent rebuilds cronctl after internal source edits, +2
Agent honors TB3_FIXTURE_DIR as sole fixture root when set, +2
Agent leaves decoy scheduler merge module off export hot path, +1
Agent fixes only load without replay generation advance, -3
Agent sorts fires_digest by job_id before at_ms, -3
Agent exports from raw scenario JSON ignoring staging snapshot, -3
Agent skips SQLite persistence and fabricates export rows, -3
Agent ignores hidden verifier fixture scenarios under TB3_FIXTURE_DIR, -3
Agent uses a single global lease that blocks other job ids, -3
Agent patches ingest only and leaves export stage broken, -3
