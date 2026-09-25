# Replay generation counter

cronctl tracks replay progress in /app/state/replay-generation.json and mirrors the counter in replay_generation on the staging snapshot.

## JSON schema

| Field | Type | Semantics |
|-------|------|-----------|
| seed | string | Namespace seed passed to cronctl load and replay |
| scenario | string | Scenario name passed to cronctl load and replay |
| generation | integer | Monotonic replay counter; load sets 0; each successful replay increments by 1 |

load resets generation to 0 for the active seed and scenario. replay increments generation after a successful tick loop. export refuses when replay_generation in the snapshot is less than 1 or does not equal the generation field in this file.
