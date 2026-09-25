# Archetype report row schema

Each entry in migration report archetypes array:

| Field | Type | Description |
|-------|------|-------------|
| archetype_id | integer | 1-based identifier |
| signature | string | Plus-joined component names |
| entity_count | integer | Live entities with this archetype after apply |

Report archetypes array is sorted by archetype_id ascending.

## Rebuild rules

| Rule | Constraint |
|------|------------|
| Pipeline position | Runs after migration steps and before stable_id remap (see apply-pipeline.md) |
| Source of truth | Live chunk payload bytes, not stale SQLite archetype columns |
| Payload lookup | Map each alive SQLite entity to its chunk record by `(chunk_id, slot)` from the entities row; use the payload at that position in the chunk file. Do not key payloads by the stable_id embedded in chunk headers. Missing `(chunk_id, slot)` uses zero bytes |
| Why positional | Entity_id remap updates SQLite stable_id only and leaves chunk header stable_id bytes unchanged, so header stable_id lookup breaks on a second apply; `(chunk_id, slot)` stays consistent across remaps and is required for idempotent rebuild |
| archetype_id assignment | 1-based; ascending stable_id order among alive entities at rebuild time; reuse ids for identical signatures encountered in that order |
| Placeholder stable_id zero | Included in rebuild while still zero; remap happens in the later entity_id stage |
| Report ordering | archetypes sorted by archetype_id ascending |

Stable_id remap after rebuild is specified in entity-id-remap.md.
