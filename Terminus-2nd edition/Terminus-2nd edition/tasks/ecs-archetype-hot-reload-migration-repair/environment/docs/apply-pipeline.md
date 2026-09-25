# Apply pipeline order

ecs-migrate apply runs the following stages in this fixed order. Later stages must not run before earlier ones complete.

| Stage | Module | When it runs |
|-------|--------|--------------|
| 1 | migrator | Layout migration steps whose order is greater than journal_replayed_from |
| 2 | archetype | Rebuild archetypes table and per-entity archetype_id from live chunk payloads |
| 3 | entity_id | Assign real stable_id values to alive placeholder rows (stable_id zero) |
| 4 | report | Read archetypes from SQLite, checksum chunk files, write migration report |
| 5 | journal | Mark replay journal committed and update migration_state |

## Archetype rebuild versus stable_id remap

Archetype rebuild runs before stable_id remap. During archetype rebuild, alive entities may still have placeholder stable_id zero in SQLite and in chunk payload headers.

| Concern | Rule |
|---------|------|
| Entity iteration order | Alive entities ordered by stable_id ascending; placeholder zero sorts before positive ids |
| Payload source | Chunk bytes keyed by stable_id embedded in each chunk record, not stale SQLite archetype columns |
| archetype_id timing | archetype_id values are written during stage 2 and are not recomputed after stage 3 |
| Report archetypes | Reflect stage 2 results; ids_remapped in the report counts only stage 3 assignments |

Entity stable_id remap rules are in entity-id-remap.md.
