# Registry namespace contract

On this system-administration page-registry control plane, ORDER is 4: a leaf or internal page may hold at most four keys before split.

## Key storage

All user keys and values live in leaf pages. Internal pages hold separator keys routing to children.

## Ordered export

Export and walk key_count use unique keys only. Duplicate keys in a leaf are invalid.

## Table namespaces

Staging tables live in /app/state/staging.json. Committed tables live in /app/state/committed.json. Export and walk read committed data only.
