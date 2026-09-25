# Archetype hash

An entity archetype is the set of `(component_id, instance_alignment)` pairs on that entity after journal replay.

## Row construction

- Collect one row per attached component: `(id, align)`.
- `align` is the instance alignment: explicit journal `align` when provided, otherwise the component spec default from `components[name].align`, otherwise entity payload override when the world JSON uses `{ "data": "...", "align": N }`.
- Sort rows by `component_id` ascending.

## Hash

SHA-256 over the concatenation of each row encoded as little-endian `u16` id bytes then little-endian `u32` align bytes. The archetype hash is the first 8 bytes of the digest interpreted as little-endian `u64`, formatted as 16 lowercase hex digits (`hash` / `archetype_hash` fields).

Different instance alignments on the same component id set must produce different hashes.
