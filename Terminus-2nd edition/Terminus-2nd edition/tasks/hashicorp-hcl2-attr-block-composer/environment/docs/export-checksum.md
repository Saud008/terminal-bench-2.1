# Export checksum

merge export writes merge-checksum.txt as a lowercase hex SHA-256 digest.

The digest input is the canonical JSON encoding of the normalized export structure (blocks array with block_type, labels, attributes, expanded_dynamics). Key ordering inside JSON objects must be sorted recursively for stable bytes.

Do not hash pretty-printed HCL text. The HCL file is for human review only; checksum integrity uses the JSON intermediate only.
