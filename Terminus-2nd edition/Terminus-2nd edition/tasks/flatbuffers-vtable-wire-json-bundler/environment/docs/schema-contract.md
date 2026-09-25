# Scene schema contract

Logical types for `/app/schema/scene.fbs`. FlatBuffers `struct` types (Vec3) use inline fixed-size layout; tables use vtables.

- **Vec3** — three `float32` components `x`, `y`, `z` stored inline with 4-byte alignment. JSON must use flatc-compatible float32 decimal rendering (see `wire-format.md`).
- **Metrics** — `distance_m` (`float32`, default `1.0` when present) and `flag_count` (`uint16`).
- **Tag** — `key` and `value` UTF-8 strings.
- **Entity** — `id`, `name`, inline `position`, optional `tags`, optional recursive `parent`, optional `metrics`.
- **Scene** — `revision` and `root` entity.

Nested `parent` chains may be multiple levels deep. A missing `tags` field is not the same as an empty tag list. Inline `position` must reflect padded layout even when preceding variable-size fields leave the raw slot unaligned.

Vtable slot indices follow declaration order in `wire-format.md`. Tag vectors in JSON export preserve wire element order.
