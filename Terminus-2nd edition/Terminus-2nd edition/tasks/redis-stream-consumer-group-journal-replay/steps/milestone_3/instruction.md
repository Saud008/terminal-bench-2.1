Finish the redisctl export rollup stage. Implement redisctl export to produce /app/output/stream-rollup.json per /app/docs/export-rollup-schema.md on top of the replay state file.

pel_distinct must count distinct pending message ids, not the sum of delivery_count. reclaim_total must stay byte-stable when export runs a second pass with the same stage file. Reopen /app/state/redis-stream-stage.json across export passes to prove idempotency.
