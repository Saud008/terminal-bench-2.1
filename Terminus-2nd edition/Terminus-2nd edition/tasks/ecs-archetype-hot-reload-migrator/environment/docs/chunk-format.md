# Chunk binary format

```json
{
  "file_name_pattern": "chunk_%04d.bin",
  "header": {
    "size_bytes": 16,
    "endianness": "big-endian",
    "fields": [
      { "name": "magic", "type": "u32", "value": "0x45435331" },
      { "name": "chunk_id", "type": "u32" },
      { "name": "layout_version", "type": "u32" },
      { "name": "payload_len", "type": "u32" }
    ]
  },
  "entity_record": {
    "endianness": "big-endian",
    "fields": [
      { "name": "stable_id", "type": "u32" },
      { "name": "component_bytes", "type": "bytes", "length": "component_stride" }
    ]
  },
  "checksum": {
    "algorithm": "sha256",
    "prefix_fields_be_u32": ["magic", "chunk_id", "layout_version", "payload_len"],
    "suffix": "payload_bytes"
  }
}
```

Checksum input: 16-byte big-endian header prefix (four u32 fields) concatenated with raw entity payload bytes. Digest encoding: lowercase hex without 0x prefix.

payload_len equals len(payload) (entity bytes only, excluding the 16-byte header).
