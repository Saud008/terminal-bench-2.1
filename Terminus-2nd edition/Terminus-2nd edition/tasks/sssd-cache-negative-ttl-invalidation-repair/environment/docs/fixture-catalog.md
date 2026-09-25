# Fixture catalog

Public bundles under /app/fixtures/ops/:

- 01-baseline.jsonl: miss, put, del lifecycle
- 02-ttl-refresh.jsonl: repeat lookup_miss before negative expiry extends TTL
- 03-domain-keys.jsonl: principals with same display name in different domains stay distinct
- 04-same-ts-order.jsonl: equal ts and seq tie-break across miss, put, del
- 05-nested-group.jsonl: nested group membership invalidates transitive users
- 06-export-expired.jsonl: expired negatives excluded from export and SQLite
- 07-lookup-hit.jsonl: lookup_hit clears negative cache rows per negative-ttl-contract
- 08-explicit-invalidate.jsonl: explicit invalidate removes positive and negative rows

Full ingest replays all public JSONL files in lexicographic filename order.

Additional operation bundles may be supplied at ingest time via absolute paths on the CLI. Domain suffix overrides for ops without an explicit domain field follow /app/docs/name-key-canonical.md.
