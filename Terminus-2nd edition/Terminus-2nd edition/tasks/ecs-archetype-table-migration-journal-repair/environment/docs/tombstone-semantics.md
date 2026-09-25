# Tombstone semantics

`tombstone` journal ops record an entity id as permanently dead for the remainder of the replay.

## Rules

- `tombstone` increments world `generation` and adds the entity id to a tombstone set.
- `spawn` for a tombstoned id is ignored (no entity row, no sparse slot allocation).
- `add_component` targeting a tombstoned id is ignored (does not resurrect the entity).
- Initial `entities` load uses the same tombstone check before insert.
- `remove_entity` frees storage but does not tombstone; a later `spawn` with the same id may succeed unless a `tombstone` op ran for that id.
- Queries exclude tombstoned ids even if a stale entity record existed.
