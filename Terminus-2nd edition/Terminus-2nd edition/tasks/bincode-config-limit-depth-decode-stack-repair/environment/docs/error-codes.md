# Error codes

| error_code | limit_kind | Meaning |
|------------|------------|---------|
| limit_exceeded | depth | composite depth budget exhausted |
| limit_exceeded | bytes | byte budget exhausted |
| invalid_varint | null | non-canonical or malformed varint |
| invalid_tag | null | unknown value tag byte |
| unexpected_eof | null | input ended before a complete value |

## Mapping rules

- Depth or byte limit breaches always map to `limit_exceeded`, never to `unexpected_eof`.
- Truncation mid-varint or mid-string with budget remaining maps to `unexpected_eof` (cursor at EOF before charging the next byte — see /app/docs/limit-contract.md).
- Non-minimal varints (redundant continuation bytes) map to `invalid_varint`.

The JSON field `limit_kind` is null unless `error_code` is `limit_exceeded`.
