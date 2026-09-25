# Platform rubric — vitess-vindex-cache-coalesce-engine

**Task folder:** tasks/vitess-vindex-cache-coalesce-engine/

Agent implements typed cache keys with vindex prefix and FNV digest per vindex-contract.md, +3
Agent drops foreign-generation rows during ingest coalesce and records coalesce_dropped, +3
Agent invalidates stale cache entries when scatter simulation returns partial failure, +3
Agent leaves route plan routes empty when scatter_ok is false, +3
Agent flushes lookup cache on rollback migration events, +3
Agent right-pads binary vindex keys into eight-byte big-endian space before range lookup, +2
Agent hashes lookup vindex shard params instead of display keys for routing space, +2
Agent writes /app/state/vindex-snapshot.json with generation and shard_map_path, +2
Agent exports routing-audit.json scatter_failures independent of route_count, +2
Agent rebuilds vtgatesim with go build after editing internal packages, +2
Agent records cache hits only when lookup generation matches shard map generation, +2
Agent patches only hasher.go while cache coalesce rules remain wrong, -3
Agent fixes scatter planner without flushing warm cache on rollback, -3
Agent edits wrap.go decoy hashing instead of typed cache key path, -2
Agent returns stale cache after partial binary scatter fault, -3
