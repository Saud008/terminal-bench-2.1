# Replay export ordering

`hitreplay export` (or the export half of `hitreplay replay`) validates `/app/state/replay-manifest.json` and the ledger header in `/app/state/tick-ledger.jsonl` per `replay-manifest.md`, then aggregates tick rows from the ledger.

Export must verify manifest epoch, row counts, and input SHA-256 bindings before sorting. Re-export after mutating the manifest without resampling is invalid.

Before writing the report, sort:

| Collection | Sort key (ascending) |
|------------|-------------------|
| `hits` | `(tick, defender_id, instance_id, attacker_id)` |
| `events` | `(tick, entity_id)` |

Do not sort by `timestamp_ms` alone; ticks may share timestamps and entity ordering is part of the audit contract.

Export reads staged ledger rows only. It must not resample animation poses or recompute collisions.
