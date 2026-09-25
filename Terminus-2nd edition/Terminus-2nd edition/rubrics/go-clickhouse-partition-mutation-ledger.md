# Platform rubric — go-clickhouse-partition-mutation-ledger

**Task folder:** tasks/go-clickhouse-partition-mutation-ledger/
**Written:** 2026-07-27T00:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent canonicalizes partition keys by sorted column names, +3
Agent orders mutation versions with numeric comparison not string sort, +3
Agent suppresses readiness when replica lag strictly exceeds threshold, +3
Agent excludes detached partitions from ready counts, +2
Agent writes idempotent SQLite rows with INSERT OR IGNORE, +3
Agent sorts staging by partition_id then mutation_version, +2
Agent implements reconcile-partitions and emit-readiness as separate stages, +2
Agent reads lag policy and anchor from config bundle, +1
Agent handles TB3_FIXTURE_ROOT override for hidden replica traps, +2
Agent rebuilds chmutled with /app/scripts/rebuild-chledger.sh after editing Go source modules, +2
Agent does not hardcode atlas JSON on disk, -3
Agent counts detached partitions toward ready_count in atlas totals, -3
Agent does not skip SQLite persistence on emit-readiness, -2
Agent does not put bug locations or fix order in instruction.md, -3
