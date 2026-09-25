# Migration report schema

Written to --report (default /app/output/migration-report.json).

```json
{
  "layout_id": "string",
  "layout_version": 0,
  "steps_applied": [
    { "order": 0, "op": "string", "component": "string", "chunks_touched": 0 }
  ],
  "archetypes": [
    { "archetype_id": 0, "signature": "string", "entity_count": 0 }
  ],
  "chunks": [
    { "chunk_id": 0, "checksum": "string", "entity_count": 0 }
  ],
  "entities_moved": 0,
  "ids_remapped": 0,
  "journal_replayed_from": 0
}
```

| Field | Type | Description |
|-------|------|-------------|
| layout_id | string | From layout manifest |
| layout_version | integer | Target to_version after apply |
| steps_applied | array | Steps executed this run |
| steps_applied[].order | integer | Step order from layout |
| steps_applied[].op | string | Step operation |
| steps_applied[].component | string | Step component field |
| steps_applied[].chunks_touched | integer | Distinct source chunks whose payloads were rewritten this step |
| archetypes | array | Rebuilt archetypes; sorted by archetype_id ascending |
| archetypes[].archetype_id | integer | 1-based archetype id |
| archetypes[].signature | string | Component signature |
| archetypes[].entity_count | integer | Live entities in archetype |
| chunks | array | One row per chunk file on disk |
| chunks[].chunk_id | integer | Chunk identifier |
| chunks[].checksum | string | SHA-256 per chunk-format.md |
| chunks[].entity_count | integer | Live entities in chunk payload |
| entities_moved | integer | Entities relocated by move steps this run |
| ids_remapped | integer | Placeholder stable_id rows assigned real ids during the entity_id stage after archetype rebuild |
| journal_replayed_from | integer | Replay cursor used at start of apply |

chunks_touched: count each source chunk at most once per step; zero when no payload changes. For move steps, count only source chunks that emitted entities, not the destination chunk that received them.

Apply stage order: migration steps sorted by ascending `order` (journal-filtered), archetype rebuild with `(chunk_id, slot)` payload lookup, stable_id remap, then report assembly. See apply-pipeline.md, archetype-rebuild.md, and entity-id-remap.md.
