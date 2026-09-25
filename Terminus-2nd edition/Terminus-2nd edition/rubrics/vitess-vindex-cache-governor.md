# Platform rubric — vitess-vindex-cache-governor

**Task folder:** tasks/vitess-vindex-cache-governor/

Agent implements typed cache keys with vindex type prefix per vindex-contract.md, +3
Agent fixes binary vindex to right-pad eight-byte big-endian space before range lookup, +3
Agent drops foreign-generation cache rows during ingest coalesce and records coalesce_dropped, +3
Agent prevents partial scatter failures from returning stale cache entries, +3
Agent flushes lookup cache on migration rollback events, +3
Agent routes using vindex type rather than vindex name when computing scatter and space, +3
Agent invalidates poisoned cache slots when scatter simulation fails, +2
Agent exports scatter_failures independently when scatter_ok is false and routes are empty, +2
Agent rebuilds vtgatesim after editing internal Go packages, +2
Agent matches independent reference shard math for hash lookup and binary batches, +2
Agent leaves /app/docs and bundled fixtures unchanged, +2
Agent hashes cache keys without vindex type disambiguator, -3
Agent masks scatter partial faults by reusing warm cache shards, -3
Agent keeps generation-2 cache rows after ingesting generation-1 shard map, -3
Agent uses little-endian or truncated binary padding for order_binary keys, -2
Agent skips cache flush on rollback migration while warm entries remain, -2
