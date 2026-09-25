# Remote-write blocks

Clients Snappy-compress an uncompressed block with this layout:

| Field | Size | Description |
|-------|------|-------------|
| magic | 4 | ASCII `RWK1` |
| body_crc32 | 4 | IEEE CRC32 of JSON body (big-endian uint32) |
| body | N | UTF-8 JSON write request |

Checksum must be validated on the uncompressed block after Snappy decode and before JSON parsing. Reject blocks whose CRC does not match.

JSON shape:

```json
{"seed":"SEED","series":[...]}
```
