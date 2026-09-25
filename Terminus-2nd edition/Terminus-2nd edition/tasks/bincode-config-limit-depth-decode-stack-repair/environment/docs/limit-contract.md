# Limit contract

The decoder receives `--max-depth` and `--max-bytes` from the CLI. Byte and depth limits interact with input reads in a fixed order documented below.

## Per-byte read order (`read_byte`)

Every single-byte read follows this sequence:

1. If the cursor is at end-of-input, stop with `unexpected_eof`. Do **not** charge the byte budget when no byte is available.
2. If the remaining byte budget is zero, stop with `limit_exceeded` with `limit_kind` `bytes`.
3. Decrement the byte budget by one and consume the byte.

Truncation with budget still available maps to `unexpected_eof`. Exhausting the byte budget while a byte is still available maps to `limit_exceeded` / `bytes`. Depth or byte limit breaches never map to `unexpected_eof`.

## Byte budget scope

After the BLIM header, every payload byte counts against `--max-bytes`, including value tag bytes, bool payloads, each varint continuation byte, string UTF-8 bodies, enum variant varints, double_option presence bytes, and nested value bodies.

Varints must be read through the byte-charging path (each continuation byte uses the same EOF-then-charge order as `read_byte`). `read_exact` charges one byte at a time for fixed-length slices.

## Composite depth — prefix bytes before `enter_composite`

Depth is charged only through `enter_composite` and restored with `leave_composite`. For composite values, the value **tag byte is always read first** (when dispatching the value). Additional prefix bytes are read **before** `enter_composite` is called:

| Tag | Kind | Read before `enter_composite` | `enter_composite` before |
|-----|------|------------------------------|---------------------------|
| 4 | vec | element-count varint (canonical, byte-charged) | decoding the first element |
| 5 | enum | variant varint (canonical, byte-charged) | decoding the nested payload value |
| 6 | double_option | outer presence byte (byte-charged) | inner presence / nested body when outer is non-zero |

Do **not** call `enter_composite` before the enum variant varint or vector element-count varint is fully read. Do **not** call `enter_composite` before the double_option outer presence byte is read.

### Vector (tag 4)

1. Read tag 4.
2. Read element-count varint with per-byte charging and canonical validation.
3. Call `enter_composite` once.
4. Decode each element in order.
5. Call `leave_composite`.

### Enum (tag 5)

1. Read tag 5.
2. Read variant varint with per-byte charging and canonical validation **before** any depth frame.
3. Call `enter_composite` once.
4. Decode the nested payload value.
5. Call `leave_composite`.

### Double option (tag 6)

1. Read tag 6.
2. Read outer presence byte with byte charging.
3. If outer is 0, return `None` with no depth frame.
4. Call `enter_composite` **once** for the outer Some shell (not a second frame for inner `Some(Some(value))`).
5. Read inner presence byte and, when non-zero, decode one nested value.
6. Call `leave_composite` exactly once on all exit paths (outer None, inner None, inner Some).

Inner `Some(Some(scalar))` does not add a second depth frame. Nested composite values inside the inner Some may consume depth when that inner value decode begins.

## Depth exhaustion

When `enter_composite` would start a new frame, if `remaining_depth` is zero, stop with `limit_exceeded` and `limit_kind` `depth` **before** pushing onto the frame stack.

Scalars (tags 0–3) never call `enter_composite`. Composite elements inside a vector charge depth when that element's composite decode begins, not for scalar elements.
