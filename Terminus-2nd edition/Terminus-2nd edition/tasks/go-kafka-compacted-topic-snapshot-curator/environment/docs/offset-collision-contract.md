# Duplicate offset collapse

When multiple records share partition and offset, keep the record with greater timestamp_ms.

On timestamp tie, keep the record whose canonical_key is lexicographically smaller.

Collapse runs after partition offset ordering.
