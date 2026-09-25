# Export checksum

The checksum file is the lowercase hex SHA-256 of the canonical governor JSON.

Canonical form sets compact_pass to 0 and serializes visible_keys column families in sorted order with keys sorted lexicographically inside each family.

Use compact JSON (no extra whitespace) for hashing.
