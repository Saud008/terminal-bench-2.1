# FlatBuffers wire contract (scene schema)

Wire layout for buffers produced by `flatc` for `/app/schema/scene.fbs`.

## Root object

Valid buffers begin with a root `uoffset_t` in the first four bytes. The root table address is that forward offset from the buffer start. The root table type is `Scene`.

## Tables and vtables

Each table begins with a **signed** `soffset_t` (little-endian `int32`) referencing its vtable. Resolve the vtable using finished-buffer relative addressing per the FlatBuffers specification — the vtable is not at a fixed forward offset from the table header alone.

Let T be the table object start in the buffer. Read signed soff at T. The vtable anchor byte index is T minus soff (soff counts backward from T in finished buffers). For field slot i with a non-zero vtable entry v, field storage begins at byte index T plus v.

The vtable layout:

| Offset | Type     | Meaning                          |
|--------|----------|----------------------------------|
| +0     | uint16   | vtable byte length               |
| +2     | uint16   | table object byte length         |
| +4+2i  | uint16   | field *i* offset from table start; `0` means absent |

Field slot indices follow **schema declaration order** in `scene.fbs` (not alphabetical name order).

### Scene slots

| Slot | Field    | Type        |
|------|----------|-------------|
| 0    | revision | uint32      |
| 1    | root     | Entity table|

### Entity slots

| Slot | Field    | Type          |
|------|----------|---------------|
| 0    | id       | uint32        |
| 1    | name     | string        |
| 2    | position | inline Vec3   |
| 3    | tags     | vector of Tag |
| 4    | parent   | Entity table  |
| 5    | metrics  | Metrics table |

### Metrics slots

| Slot | Field       | Type    |
|------|-------------|---------|
| 0    | distance_m  | float32 |
| 1    | flag_count  | uint16  |

### Tag slots

| Slot | Field | Type   |
|------|-------|--------|
| 0    | key   | string |
| 1    | value | string |

## Indirection offsets

`uoffset_t` values are stored at the field location and reference data relative to that storage site in finished file buffers: the target address is the field slot address plus the unsigned offset. This applies to strings, vectors, and nested tables.

## Inline structs

Struct fields (for example `Vec3`) are stored inline in the table object. The vtable entry points at the aligned inline storage; preceding variable-size fields may insert padding before the struct slot.

## Strings and vectors

Strings and vectors are length-prefixed blocks reached through a `uoffset_t` at the field slot. A vtable field offset of `0` means the field is absent.

Vectors of tables store one `uoffset_t` per element; element stride follows FlatBuffers table-vector layout for the schema.

## JSON output

Emit a single JSON object with `revision` and nested `root`. Optional absent fields (`tags`, `parent`, `metrics`) must match `flatc --json --strict-json --defaults-json` omission semantics. Strings use UTF-8.

### float32 rendering

All `float32` wire values must decode to IEEE-754 single precision. Stdout decimal text should match `flatc --json --strict-json --defaults-json` for the same buffer.

## Errors

Return a non-zero exit code when the buffer is truncated, root offset is invalid, vtable is out of range, or an indirection cannot be followed safely.
