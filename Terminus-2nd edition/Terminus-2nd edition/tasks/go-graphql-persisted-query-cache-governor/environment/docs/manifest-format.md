# Operation manifest format

Each manifest file describes one automatic persisted query (APQ) operation registered at the GraphQL gateway edge. JSON uses sorted keys and trailing newline.

Required fields:

- operation_id (string)
- operation_hash (hex sha256 of normalized query_text)
- schema_hash (string, must match tenant schema unless compound mode)
- query_text (string)
- registered_at_ms (integer epoch milliseconds)
- last_seen_ms (integer epoch milliseconds)
- manifest_version (integer, must be 1)

## Operation hash normalization

Before hashing:

1. Trim leading and trailing whitespace from query_text.
2. Collapse internal whitespace runs to a single ASCII space.
3. operation_hash = lowercase hex(sha256(normalized_bytes)).

Ingest rejects manifests where recomputed hash differs from operation_hash field.

Manifest files are loaded in lexicographic filename order. Staging operations preserve that order before digest computation sorts by operation_id for staging_digest only.
