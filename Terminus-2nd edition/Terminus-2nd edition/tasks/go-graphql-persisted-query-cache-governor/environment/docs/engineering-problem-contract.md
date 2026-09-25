# APQ policy admission contract — go-graphql-persisted-query-cache-governor

Task identity: gql-apq-cache-governor-v1

## Operational objective

Construct an APQ policy admission workflow that materializes four linked artifacts on the working /app baseline:

- /app/state/pq-staging.json after ingest
- /app/state/pq-ledger.db after reconcile
- /app/work/reconcile-report.json after reconcile
- /app/output/pq-audit.sqlite after export-audit

The task is about keeping those artifacts consistent as persisted-query manifests move through ingest, policy reconcile, and sealed audit export. Governing behavior is verified through artifact contents and cross-stage integrity invariants, not through any single isolated CLI surface.

## Trust boundary

GraphQL automatic persisted query (APQ) edge nodes cache query bodies keyed by operation_hash. Stale schema fingerprints, unbounded tenant growth, and TTL drift cause edge nodes to serve incompatible or expired persisted queries unless a governor validates manifests, enforces per-tenant APQ quotas, and exports audit evidence.

## Refusal modes

| Failure | Observable |
|---------|------------|
| Hash drift | operation_hash computed without whitespace normalization accepts wrong APQ body |
| Schema mismatch | manifest schema_hash diverges from tenant registry |
| Quota overflow | active APQ count exceeds max_active without LRU eviction |
| TTL stale | last_seen_ms anchor ignored; expired queries remain active |
| Audit undercount | export meta counts staging rows instead of ledger rows |

## Non-goals

This is not BGP route dampening, Kafka compaction, chat replay, or generic cache TTL tooling. The governor reasons about GraphQL operation manifests, tenant policy state, and APQ audit evidence only.
