# Merkle proof rules

RFC 6962 domain separation applies:

- Leaf digest uses prefix byte 0x00 before leaf_input bytes.
- Internal node digest uses prefix byte 0x01 before left then right child digests.

Inclusion audit_path steps name sibling hash hex and side left or right relative to the running digest.
