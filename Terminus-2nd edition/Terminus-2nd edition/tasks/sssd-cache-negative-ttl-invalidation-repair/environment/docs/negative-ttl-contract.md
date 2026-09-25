# Negative cache TTL contract

When kind is lookup_miss, the cache records a negative entry for the canonical principal key.

On the first miss at ts T, expires_at is T plus negative_ttl_sec from /app/config/sssdcache.json.

When the same principal misses again before expires_at, expires_at must be reset to the new ts plus negative_ttl_sec (refresh). A retry after expiry creates a new negative window.

lookup_hit removes any negative entry for that principal.

Export and snapshot stats count negative_refreshed when a miss extends an unexpired negative.
