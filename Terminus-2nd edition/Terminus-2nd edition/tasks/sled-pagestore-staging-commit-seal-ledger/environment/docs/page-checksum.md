Each page record in /app/state/page_registry.json stores header.generation and body.

checksum is 32-bit FNV-1 (not FNV-1a). Start with offset basis 0xFFFFFFFF. For each byte in order, update acc as acc = (acc * 16777619) XOR byte, keeping acc in 32 bits.

Hash the eight little-endian bytes of generation first, then every byte of body in order. The stored checksum must match this value for each page record.
