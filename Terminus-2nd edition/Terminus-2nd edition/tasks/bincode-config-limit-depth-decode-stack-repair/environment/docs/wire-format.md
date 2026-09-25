# BLIM wire format

Every payload begins with the five-byte header `BLIM\x01`. Bytes after the header are a single root value.

## Value tags (one byte each)

| Tag | Name | Body |
|-----|------|------|
| 0 | null | none |
| 1 | bool | one byte: 0 false, non-zero true |
| 2 | u32 | unsigned varint (see /app/docs/limit-contract.md) |
| 3 | string | varint byte length, then UTF-8 bytes |
| 4 | vec | varint element count, then count values back-to-back |
| 5 | enum | varint variant tag, then one nested value |
| 6 | double_option | presence byte, optional inner presence byte, optional nested value |

## Enum and double_option

Tag 5 wraps an arbitrary nested value. Tag 6 encodes Option of Option:

- Outer presence 0 means `None` (no inner bytes).
- Outer presence non-zero: read inner presence byte.
  - Inner 0 means `Some(None)`.
  - Inner non-zero: decode one nested value as `Some(Some(value))`.

## Varint canonical form

Unsigned varints use 7 data bits per byte with high bit set on all but the final byte. The encoding must be **minimal**: no redundant continuation bytes. Example: integer 0 is exactly one byte `0x00`, never `0x80 0x00`.

Decoders must reject non-canonical varints with error_code `invalid_varint`.

## Composite depth

Depth limits apply when entering composite containers documented in /app/docs/limit-contract.md. Scalar tags 0–2 do not consume depth budget beyond their tag byte and immediate payload bytes.
