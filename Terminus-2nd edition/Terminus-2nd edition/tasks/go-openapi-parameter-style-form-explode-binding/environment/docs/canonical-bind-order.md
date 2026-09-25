# Canonical bind parameter order

Before staging to `/app/state/bind-snapshot.json`, paramgate must canonicalize the bound parameter map produced by the query, path, and header parsers.

## Top-level parameter keys

Sort top-level `params` keys lexicographically ascending by UTF-8 byte order.

## Nested object fields

For any parameter value that is an object (for example `filter` or `window`), sort nested field keys lexicographically ascending before writing the snapshot and before emission.

Array element order must be preserved. Scalar values are unchanged.

## Pipeline position

Canonicalization runs after all binding parsers finish and before `WriteBindSnapshot`. The HTTP success payload must read the canonical values from the staged snapshot, not from pre-canonical in-memory maps.

See `/app/docs/bind-snapshot.md` and `/app/docs/param-binding-contract.md`.
