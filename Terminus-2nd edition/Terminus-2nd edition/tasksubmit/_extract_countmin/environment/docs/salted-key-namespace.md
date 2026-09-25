# Salted key namespace

Count-Min Sketch row indices hash a namespaced key formed by concatenating namespace_salt, the single-byte delimiter 0x1F, and the raw query key UTF-8 bytes. The hash seed and row index feed the same row hash function documented in conservative-merge-contract.md.

Two keys that differ only by namespace_salt must map to different row indices. Export estimates must query using the bundle namespace_salt from staging, not the raw key alone.
