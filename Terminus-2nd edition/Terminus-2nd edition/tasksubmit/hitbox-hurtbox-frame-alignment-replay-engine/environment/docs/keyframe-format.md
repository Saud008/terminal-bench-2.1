# Keyframe animation format

Animation clips are JSONL under `/app/fixtures/animations/`. Each non-empty line is one keyframe object.

## Required fields

| Field | Type | Meaning |
|-------|------|---------|
| `entity_id` | string | Entity that owns the bone |
| `bone` | string | Bone name sampled for hitboxes |
| `frame` | integer | Animation frame index (0-based) |
| `pos` | `[x,y,z]` | Bone position in world space |
| `rot` | `[x,y,z,w]` | Bone orientation quaternion (x,y,z,w) |
| `instance_id` | integer | Attack instance id carried into hit events |

Keyframes for the same `(entity_id, bone)` pair must be sorted by ascending `frame` when read from disk. Sampling interpolates between the bracketing keyframes at the frame derived from each tick per `frame-index.md`.

Rotation blending must use quaternion slerp, not Euler component lerp. Position uses linear interpolation between bracketing keyframes.
