# Vindex space and shard resolution

Each vindex type maps a query key into a uint64 routing space before shard range lookup.

Hash vindex: FNV-1a 64-bit digest of the UTF-8 key string.

Binary vindex: decode hex (optional 0x prefix). Pad the decoded bytes to eight bytes big-endian in the uint64 space: place decoded bytes in the least significant end of an eight-byte buffer (right-aligned), then interpret as big-endian uint64. Values longer than eight bytes use only the last eight bytes.

Lookup vindex: map the key through the vindex params table to a shard name, then hash that shard name with FNV-1a for space placement when cross-checking ranges. When the supplied key is not present in the vindex params table, routing space is zero and the query still produces a route (ResolveShard applies to space zero).

Shard map JSON lists shards with inclusive-start exclusive-end hex ranges on uint64 space. ResolveShard picks the first range where start <= space < end; if none match, use the last shard in file order.

Cache lookup keys must include the vindex type disambiguator: concatenate type, colon, and FNV-1a hex of the raw key string (not the space value). Two different vindex types with the same display key must not share a cache slot.
