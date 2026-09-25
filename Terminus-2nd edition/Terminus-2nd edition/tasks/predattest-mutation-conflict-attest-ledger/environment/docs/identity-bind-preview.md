# Identity bind preview

Blank node labels (`_:name`) are resolved to concrete `0x` uids. The first
time a label is seen it is allocated a fresh uid (`0x1`, `0x2`, … in
allocation order); the binding persists for the rest of the wave.

When an edit sets `bind: true` and supplies a non-empty `bind_on`, the blank
node is an **upsert**: it must attach to an existing node instead of
allocating a new one when a match exists.

## Match rule

Consider existing nodes in ascending uid order. A node matches when **every**
key in `bind_on` holds:

- the node has a scalar `key.attr` whose value equals `key.value`; and
- if `key.facets` is non-empty, the node's stored facets for that attr, when
  each facet list is sorted by `(key, value)`, equal the sorted `key.facets`
  (same length, same `key`/`value` pairs in order).

The first matching node (lowest uid) binds the blank label and is returned.
If no node matches, a fresh uid is allocated as usual. An edit without `bind`
or with an empty `bind_on` is never an upsert.

Facets are compared by their `(key, value)` content only; their order in the
record is irrelevant because both sides are sorted before comparison.
