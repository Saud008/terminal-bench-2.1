# Wire identifier layout

A minted admission ticket is a twelve-byte BSON-compatible wire identifier: four big-endian Unix-time bytes, five FNV-1a machine-binding bytes, and a three-byte per-second counter. `/v1/mint` emits lowercase 24-character hex values. A backward clock or a counter past `0xFFFFFF` is denied with HTTP 409. `/v1/wire-doc` embeds a supplied ticket in BSON type `0x07` and returns base64 bytes. The ObjectId element must use BSON field order `type`, then `e_name` (`\x07_id\x00`), then the twelve identifier bytes.
