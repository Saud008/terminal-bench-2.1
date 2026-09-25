# Digest-sealed attestation binding

Integrity gate for sealed publish: the import_reorder_digest is SHA-256 over the concatenation of canonical import rows after tuple-rank reorder.

Each row contributes module_len as u8, module bytes, name_len as u8, name bytes, and the resolved module-type index as u16 little-endian.

Hashing the pre-canonical wire bytes or hashing before alias-aware type resolution is incorrect.
