# Vtable decode contract

All vtable header and slot scalars on the wire are little-endian.

When decoding vtable_len, object_size, or voffset_t slot values, implementations must use little-endian byte order.

Big-endian or native-endian reads produce incorrect slot maps in the staging ledger on little-endian hosts and must not be used.

The first decoded slot for a root table with one field must equal eight when the bundled scene_a wire is ingested.
