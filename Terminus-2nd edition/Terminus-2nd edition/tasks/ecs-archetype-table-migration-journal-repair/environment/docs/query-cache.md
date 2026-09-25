# Query cache

`archectl query` may memoize results inside a process. `query-batch` runs multiple queries sequentially in one process.

## Cache key

Hash of the sorted component id list **and** the world's storage `generation` after full replay (initial entity load, then journal). A cache entry is valid only when its stored generation equals the current generation.

When `generation` changes (journal mutation, spawn, component add/remove, tombstone, etc.), prior entries for that query must miss and recompute.

## Cross-world isolation

Batch steps load different world specs. Cache keys must incorporate generation per replayed world so a query on world B cannot return entity ids computed for world A with the same component id list.

`cache_hit` is informational; tests compare `entities` and `generation` against a fresh replay, not against `cache_hit`.
