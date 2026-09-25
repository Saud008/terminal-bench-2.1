# Fixture catalog

Bundled replay logs live under /app/fixtures/replay/. Each file is JSONL ordered by seq (tie breaks equal seq). Line counts and event mixes vary by file; use them to validate replay against the contracts in /app/docs/.

| File | Lines | Primary ops |
|------|------:|-------------|
| 001-base.jsonl | 5 | discover, offer, ack |
| 002-renewal-skew.jsonl | 7 | offer, ack, renew, tick |
| 003-duid-collision.jsonl | 5 | discover, offer, ack |
| 004-decline-tentative.jsonl | 4 | discover, offer, decline |
| 005-ack-replay.jsonl | 5 | request, ack |
| 006-ip-change-checkpoint.jsonl | 5 | ack, replay_checkpoint |
| 007-release.jsonl | 4 | ack, release |
| 008-multi-renew.jsonl | 7 | ack, renew, tick |

When TB3_REPLAY_DIR is set to an absolute directory, replay reads logs from that directory instead of /app/fixtures/replay/.
