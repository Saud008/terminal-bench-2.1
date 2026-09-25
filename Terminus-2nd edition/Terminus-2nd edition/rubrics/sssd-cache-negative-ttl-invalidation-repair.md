# Platform rubric — sssd-cache-negative-ttl-invalidation-repair

**Task folder:** tasks/sssd-cache-negative-ttl-invalidation-repair/

Agent rebuilds sssdcache with go build -mod=vendor after editing replay Go modules, +2
Agent refreshes negative TTL expires_at when lookup_miss repeats before expiry, +3
Agent canonicalizes cache keys with lowercased domain and preserved principal name case, +3
Agent applies same-timestamp replay priority from replay-ordering.md across all operation kinds, +3
Agent invalidates transitive group members when nested_invalidation is enabled in config, +3
Agent filters expired negatives from export active_negatives using evaluated_at_ms, +3
Agent handles lookup_hit operations that clear negative cache rows per negative-ttl-contract, +2
Agent handles explicit invalidate operations that remove positive and negative rows, +2
Agent persists only active negatives into SQLite negative_cache at ingest time, +2
Agent patches export rollup or wrap merge decoy helpers while replay ordering stays wrong, -3
Agent fixes lookup_miss TTL only while same-ts invalidate and lookup_hit ordering remains broken, -3
Agent edits cache key logic while domain-scoped negatives still collide across domains, -2
