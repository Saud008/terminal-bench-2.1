# Zone cache invalidation

zonefrag caches compiled snapshot JSON under /app/state/.zone-cache to accelerate repeated compiles.

## Cache key

The cache key must incorporate tree path, seed, include_fingerprint, and the reload flag.

The include_fingerprint is computed in four steps:

1. Start a parts list with the manifest master path exactly as stored in manifest.json.
2. Recursively scan every .zone file under the tree, sort those paths by relative POSIX path, and skip the master path entry.
3. For each remaining .zone file, append REL_PATH:HASH16 where HASH16 is the first 16 lowercase hex characters of the file content SHA-256 digest.
4. Join the parts list with the literal | separator, then take the lowercase hex SHA-256 digest of that UTF-8 string.

The reload flag is 0 for normal compile or ingest runs and 1 when --reload is passed. Compute the cache key as the lowercase hex SHA-256 digest of the UTF-8 string tree:seed:include_fingerprint:reload_flag.

## Invalidation

When any non-master .zone file changes, include_fingerprint changes and prior cache entries must not be reused even if tree path and seed are unchanged.

Partial include edits without master changes still require a fresh merge.

## Snapshot fields

Every snapshot stores include_fingerprint and zone_hash. zone_hash covers origin, processing_order, records, soa_serial, and include_fingerprint per digest-contract.md.
