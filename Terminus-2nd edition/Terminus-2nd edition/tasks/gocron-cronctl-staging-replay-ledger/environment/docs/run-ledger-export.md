# Run ledger export

Export writes JSON with seed, scenario, executions, fire_count, and dedup_count.

## Execution row fields

Each execution object includes job_id, fired_at_ms, status, lock_held, and deduped.

fired_at_ms uses absolute Unix epoch milliseconds UTC, matching planned_fires at_ms semantics.

## Execution ordering

SQLite `executions` rows and export `executions[]` must be ordered by `fired_at_ms` ascending, then `job_id` ascending (lexicographic). Store.List and export must preserve that order; graders compare rows in this sequence.

## Status literals

Persist these exact lowercase status strings in SQLite and in export JSON:

| status | Meaning |
|--------|---------|
| fired | Job started and lock acquired |
| success | Completed normally (internal tracker only; may not appear in export fixtures) |
| deduped | Suppressed by singleton or singleton_group coalescing |
| aborted | In-flight run interrupted by reschedule event |
| panic | Panic event recorded; lock_held must be false |

Reschedule events while a job is running must yield aborted on the in-flight row, never success or alternate strings such as in_flight_rescheduled.

After panic events, lock_held must be false on the panic row and the distributed lease must not remain held.

## Export gates

export reads /app/state/replay-snapshot.json and /app/state/replay-generation.json before building output.

export fails when engine is not croncalc, fires_digest does not match a recomputation from planned_fires, or replay_generation in the snapshot does not equal the generation file after replay.

fire_count counts executions where deduped is false. dedup_count counts executions where deduped is true.
