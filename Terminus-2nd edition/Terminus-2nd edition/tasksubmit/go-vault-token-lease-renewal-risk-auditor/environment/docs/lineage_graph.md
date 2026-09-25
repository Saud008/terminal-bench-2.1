# Lineage graph schema

## Staged fields

| Field | Type | Notes |
|-------|------|-------|
| lineage_root | string | Root token id, or a prefixed identifier (`orphan:…`, `cycle:…`) |
| lineage_depth | int | Parent hops to `lineage_root`; `-1` marks cycle rows |
| is_orphan | bool | Orphan classification for the row |
| delegated_parent | string | Effective parent token id when lineage resolves completely; otherwise empty |

Event `orphan` and `parent_id` participate in lineage classification. Ancestor lookups use each ancestor's latest renewal in the corpus.

Two orphan cases are distinct:

- **Orphan severance** — `orphan` is true: drop the parent edge; `lineage_root` is the token's own id (no `orphan:` prefix); `is_orphan` true; depth 0. Example: `hvs.SEV` with `orphan=true` and parent `hvs.ROOT` yields `lineage_root` `hvs.SEV`.
- **Missing ancestor** — `orphan` is false but `parent_id` or a walked ancestor is absent from the corpus: `lineage_root` is `orphan:` + token id; `is_orphan` true; depth 0. Example: `hvs.ORPH` with a missing parent yields `orphan:hvs.ORPH`.

## lineage_edges (rollup)

Edges use `parent_token` / `child_token` and are emitted only for staged rows with a non-empty `delegated_parent`.
