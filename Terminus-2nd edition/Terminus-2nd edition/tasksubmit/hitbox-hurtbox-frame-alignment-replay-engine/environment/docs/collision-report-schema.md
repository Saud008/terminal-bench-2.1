# Collision report schema

`hitreplay export` writes `/app/output/collision-report.json` after validating the replay manifest and aggregating `/app/state/tick-ledger.jsonl`.

## Top-level object

| Field | Type | Meaning |
|-------|------|---------|
| `layout_version` | integer | Report schema version (always `1`) |
| `tick_rate` | integer | Tick rate from manifest |
| `anim_fps` | integer | Animation FPS from manifest |
| `hits` | array | Sorted hit events |
| `events` | array | Sorted replay events |

## Hit event

| Field | Meaning |
|-------|---------|
| `tick` | Simulation tick |
| `frame` | Animation frame from `frame-index.md` |
| `timestamp_ms` | `tick * 1000 / tick_rate` |
| `attacker_id` | Attacking entity id |
| `defender_id` | Defending entity id |
| `instance_id` | Attack instance from keyframes |
| `bone` | Attacker bone name |

## Replay event

| Field | Meaning |
|-------|---------|
| `tick` | Simulation tick |
| `frame` | Animation frame |
| `timestamp_ms` | Milliseconds from tick |
| `entity_id` | Entity sampled |
| `bone` | Bone name (empty string when unused) |
| `event_type` | Always `pose_sample` for bundled fixtures |

Sorting rules are defined in `replay-export.md`.
