# Feed-normalize cache schema

Path: /app/state/feed-normalize-cache.json

Fields:
- load_generation: monotonically increasing unsigned integer shared across all seeds; starts at 1 on the first compile-feeds run after an empty or missing cache, and increments by 1 on every subsequent compile-feeds call regardless of seed or bundle
- seed: opaque seed string from CLI (active snapshot seed)
- bundle: bundle name matching fixtures
- records: array of feed-cache rows with cidr, country, asn, feed_id, lineage_id

The cache file holds one active seed/bundle snapshot at a time. Switching seeds overwrites seed, bundle, and records but continues the same global load_generation sequence.
