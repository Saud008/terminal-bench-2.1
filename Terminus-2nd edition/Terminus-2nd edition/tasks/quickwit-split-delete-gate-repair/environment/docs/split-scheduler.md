# Split scheduler

Publishing a split must follow this order:

1. Apply all pending delete-by-query tombstones to the inverted index and doc store (see /app/docs/delete-gate.md).
2. Flush the pending document buffer into shard storage.
3. Append the split entry to the object store manifest with lineage per /app/docs/manifest-format.md.
4. Invalidate any hot-cache entries superseded by the new split generation.

split-meta.json records the latest published split_id and publish_seq incrementing from 1.

The scheduler must not publish a shard while tombstones for the same publish generation remain unapplied.
