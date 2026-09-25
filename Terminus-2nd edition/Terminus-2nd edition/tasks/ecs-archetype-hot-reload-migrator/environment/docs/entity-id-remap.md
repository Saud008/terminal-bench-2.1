# Entity stable_id remap

After migration steps and archetype rebuild, assign durable stable_id values to alive entities that still carry placeholder stable_id zero.

## Tombstone set

Load all stable_id values from the tombstones table, sorted ascending. These ids are reserved and must never be reassigned to a live entity.

## Remap algorithm

| Step | Action |
|------|--------|
| 1 | Let tombstones be the set of tombstoned stable_id values |
| 2 | Let max_id be COALESCE(MAX(stable_id), 0) from entities (includes placeholder zero rows) |
| 3 | Let next_id start at max_id + 1 |
| 4 | Select alive entities with stable_id zero ordered by SQLite rowid ascending |
| 5 | For each selected rowid | While next_id is in tombstones, increment next_id |
| 6 | | UPDATE entities SET stable_id = next_id WHERE rowid matches the current row |
| 7 | | Increment ids_remapped, then increment next_id |
| 8 | Return ids_remapped |

## Constraints

| Rule | Detail |
|------|--------|
| SQLite only | UPDATE entities rows in /app/data/ecs_meta.db; do not rewrite chunk files under /app/data/chunks/ |
| Chunk bytes unchanged | stable_id values embedded in chunk payload headers stay as written during migration and archetype rebuild |
| Row targeting | Update by SQLite rowid, not by stable_id zero alone, so only the intended placeholder row changes |
| Tombstone skip | If next_id collides with a tombstoned id, advance next_id until it is free |
| No reuse | Never assign a tombstoned stable_id to an alive entity |
| Idempotent replay | When no alive placeholder rows remain, ids_remapped is zero |

## Fixture example

Bundled state has alive entities with stable_id 1 through 5, one alive placeholder with stable_id zero, and tombstone 42. max_id is 5, next_id starts at 6. Tombstone 42 does not block 6. The placeholder remaps to stable_id 6 and ids_remapped is 1.
