# SSSD cache operation JSONL

Each line is one JSON object applied in replay order.

Required fields on every record:

- ts: integer epoch milliseconds when the operation was logged
- seq: monotonic sequence within a bundle (tie-breaker at equal ts)
- kind: one of lookup_miss, lookup_hit, cache_put, cache_del, group_add_member, invalidate

Identity fields:

- domain: DNS domain suffix for the principal (case preserved in the log; canonical form lowercases domain only)
- name: principal name (case preserved; never lowercased in the cache key)

Group fields (group_add_member):

- group: group name
- member: user or nested group name

Positive cache (cache_put):

- value: opaque string stored for the principal

invalidate:

- name: user principal to invalidate when explicit invalidation is logged

Files are UTF-8 JSONL sorted by filename; replay sorts all records by (ts, seq) then applies same-ts priority from /app/docs/replay-ordering.md.
