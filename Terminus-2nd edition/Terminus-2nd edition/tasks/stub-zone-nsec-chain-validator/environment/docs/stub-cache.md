# Stub denial cache

The validator keeps an in-memory cache of denial outcomes to model stub resolver reuse.

Cache keys combine canonical qname and qtype. Two queries with the same owner name but different qtypes must not share a cached proof outcome.

When a query includes soa_serial, call serial observation before lookup. If the new serial is lower than the previous high-water serial, flush all cached entries and reset hit counts before processing that query.

cache_hits in the report counts how many queries were served entirely from cache without re-walking proofs. Serial regression with a changed proof must not increment hits from stale entries.
