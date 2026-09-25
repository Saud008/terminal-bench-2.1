# Export rollup schema

redisctl export reads /app/state/redis-stream-stage.json and writes /app/output/stream-rollup.json.

stream_lengths maps stream name to entry count. groups is an array of objects with stream, group, pel_distinct, reclaim_total.

pel_distinct counts distinct message ids still in the group PEL, not the sum of delivery_count values.

export_pass records the pass number from redisctl export --pass N. reclaim_total must be idempotent across repeated export passes with the same stage file. A second pass must not double the reclaim_total values.
