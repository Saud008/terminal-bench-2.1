# Merge idempotency

merge export accepts --pass N. Pass 1 compacts staging into /app/output/segment-stats.json and persists merge state at /app/state/merge-state.json.

Pass 2 with unchanged staging must reproduce identical delete_bits and merge-checksum.txt as pass 1. Re-OR-ing delete bits from staging into persisted merge state on later passes duplicates tombstones and breaks idempotency.

The checksum excludes merge_pass; it is SHA-256 hex over canonical JSON of live_max_doc, delete_bits, and terms with u8 norms.
