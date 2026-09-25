# Replay ordering at equal timestamp

Primary sort: ascending ts, then ascending seq.

When ts and seq are equal, apply kinds in this priority (lower number first):

1. lookup_miss
2. cache_put
3. group_add_member
4. invalidate
5. cache_del
6. lookup_hit

Deletes must not run before inserts or negative misses at the same timestamp, or a put followed by del at the same ts would leave stale positives.
