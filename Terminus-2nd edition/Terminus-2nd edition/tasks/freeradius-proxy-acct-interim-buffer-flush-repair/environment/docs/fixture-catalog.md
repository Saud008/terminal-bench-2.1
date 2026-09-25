# Fixture catalog

Public bundles under /app/fixtures/radius/:

| File | Exercises |
|------|-----------|
| 01-baseline.jsonl | Start, interim, stop with 300s interim |
| 02-interim-precedence.jsonl | Session-Timeout 3600 with Acct-Interim-Interval 120 |
| 03-nas-reboot.jsonl | Same Acct-Session-Id, new Acct-Unique-Session-Id after reboot |
| 04-flush-order.jsonl | Two sessions; buffered interims flush in one batch ordered by session_start_ts |
| 05-interim-storm.jsonl | Rapid interim updates within one session |
| 06-stop-pending.jsonl | Stop forces flush of pending interim |

Additional JSONL bundles outside this catalog may be used during verification; agents should implement behavior from the contract docs, not from extra fixture locations.
