# Replay staging

load writes /app/state/replay-snapshot.json after ingest.

## Snapshot fields

| Field | Semantics |
|-------|-----------|
| seed, scenario | Namespace identifiers passed to cronctl |
| location | Scheduler default location copied from config at load time |
| engine | Must be the literal string croncalc when fires were planned with the croncalc package |
| planned_fires | Array of job_id and at_ms objects sorted by at_ms then job_id |
| at_ms | Absolute Unix epoch milliseconds in UTC for the planned instant (not an offset from window_start) |
| fires_digest | Lowercase 16-digit hex FNV-1a 64-bit digest of UTF-8 lines job_id:at_ms sorted as in planned_fires, one line per fire, trailing newline after each line |
| replay_generation | Integer generation counter; load sets 0; successful replay bumps generation in both this field and /app/state/replay-generation.json |

planned_fires must be derived from the same fire-time engine used by replay (location-aware cron expansion via the croncalc package).

export cross-checks that every non-deduped execution fired_at_ms appears in planned_fires for that job.

## Replay generation file

/app/state/replay-generation.json holds seed, scenario, and generation. Field types and counter semantics are defined in /app/docs/cronledger-counter-schema.md.

| Field | Type | Semantics |
|-------|------|-----------|
| seed | string | Namespace seed passed to cronctl load and replay |
| scenario | string | Scenario name passed to cronctl load and replay |
| generation | integer | Monotonic replay counter; load sets 0; each successful replay increments by 1 |

replay increments generation after a successful tick loop. export refuses when replay_generation in the snapshot is less than 1 or does not equal the generation field in this file.
