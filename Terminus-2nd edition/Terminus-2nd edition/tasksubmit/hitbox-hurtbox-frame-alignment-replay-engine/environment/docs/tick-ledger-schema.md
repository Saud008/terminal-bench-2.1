# Tick ledger staging schema

Every `hitreplay sample` (or `hitreplay replay`) run writes `/app/state/tick-ledger.jsonl` before export may run. Export must aggregate this file; re-running collision detection during export bypasses staging and is incorrect.

See `replay-manifest.md` for manifest fields and the ledger header line written as the first JSONL record.

## Header line

Line 1 is always a header object:

```json
{"_kind":"header","epoch":1,"row_count":121}
```

`epoch` must match `/app/state/replay-manifest.json`. `row_count` is the number of tick rows that follow.

## JSONL tick row shape

Starting at line 2, one JSON object per line, one row per simulated tick (0 through `max_tick` inclusive):

```json
{"tick":0,"hits":[],"events":[{"tick":0,"frame":0,"timestamp_ms":0,"entity_id":"dummy","bone":"","event_type":"pose_sample"}]}
```

| Field | Meaning |
|-------|---------|
| `tick` | Simulation tick index |
| `hits` | Hit events detected on this tick (see `collision-report-schema.md`) |
| `events` | Pose sample markers for entities present in the scenario |

Tick rows are written in ascending `tick` order during sampling. `finalize_manifest` rewrites the file to prepend the sealed header without reordering tick rows.
