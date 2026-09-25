# Apply pipeline order

ecs-migrate apply runs the following stages in this fixed order. Later stages must not run before earlier ones complete.

| Stage | Module | When it runs |
|-------|--------|--------------|
| 1 | migrator | Layout migration steps whose `order` is greater than journal_replayed_from, processed in ascending `order` |
| 2 | archetype | Rebuild archetypes table and per-entity archetype_id from live chunk payloads |
| 3 | entity_id | Assign real stable_id values to alive placeholder rows (stable_id zero) in SQLite only; chunk files are not rewritten |
| 4 | report | Read archetypes from SQLite, checksum chunk files, write migration report |
| 5 | journal | Mark replay journal committed and update migration_state |

## Migration step execution order

Within stage 1, migration steps from the layout manifest must be processed in ascending `order` field sequence. Sort `migration_steps` by `order` ascending before filtering and applying. Do not rely on JSON array position alone. Only steps with `order` greater than the journal replay start cursor are applied; among those remaining steps, lower `order` values run first.

## Archetype rebuild versus stable_id remap

Archetype rebuild runs before stable_id remap. During archetype rebuild, alive entities may still have placeholder stable_id zero in SQLite and in chunk payload headers.

| Concern | Rule |
|---------|------|
| Entity iteration order | Alive entities ordered by stable_id ascending; placeholder zero sorts before positive ids |
| Payload source | Chunk payload bytes looked up by SQLite `(chunk_id, slot)`, not by stable_id embedded in chunk headers, and not from stale SQLite archetype columns |
| archetype_id timing | archetype_id values are written during stage 2 and are not recomputed after stage 3 |
| Report archetypes | Reflect stage 2 results; ids_remapped in the report counts only stage 3 assignments |

Entity stable_id remap rules are in entity-id-remap.md. Payload lookup details are in archetype-rebuild.md.
