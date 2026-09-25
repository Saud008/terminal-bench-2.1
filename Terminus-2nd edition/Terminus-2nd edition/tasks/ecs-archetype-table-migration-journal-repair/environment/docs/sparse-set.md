# Sparse entity slots

Each live entity occupies a sparse slot used for `slot_generation` in migrate exports.

## Allocation

- New entity: append a slot with `generation = 0`.
- Recycled slot (entity removed, index on free list): increment that slot's `generation` before reassigning the entity id, then mark alive.

`slot_generation` in export is the slot's current generation counter for that entity id after journal replay. A recycled id (for example entity 99 after remove + spawn) must report `slot_generation >= 1`.
