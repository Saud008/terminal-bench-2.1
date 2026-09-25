# Staging ledger format

The binary ledger at /app/state/vtable-ledger.bin uses this layout:

- magic FBLE
- version u32 little-endian, value one
- ingest_seq u32 little-endian, incremented on each ingest call
- entry_count u32 little-endian

Each entry stores source filename, original wire bytes, root records, and gap spans.

Each root record stores table_off, vtable_off, vtable_len, object_size, and decoded slot offsets.

Ledger writers must validate vtable_len is at least four bytes before reading field presence slots from the vtable. Reading presence slots when vtable_len is truncated is incorrect.

Ingest lists entries in sorted source filename order.
