# Staging snapshot format

Path: /app/state/pq-staging.json

JSON compact encoding with trailing newline (no indentation).

Top-level keys must serialize in this exact order:

1. engine
2. tenant_id
3. scenario
4. schema_hash
5. operation_count
6. operations
7. staging_digest

Fields:

- engine (string, pqgov-v1)
- tenant_id
- scenario
- schema_hash (tenant or compound expected hash)
- operation_count (length of operations)
- operations (array of staged rows sorted by operation_id ascending)
- staging_digest (hex sha256)

Each staged operation includes operation_id, operation_hash, schema_hash, registered_at_ms, last_seen_ms.

## staging_digest

Payload before hash:

Serialize a compact JSON object whose keys appear in this exact order:

1. tenant_id
2. scenario
3. schema_hash
4. operations

The operations array must already be sorted by operation_id ascending, and each operation object must serialize fields in this exact order: operation_id, operation_hash, schema_hash, registered_at_ms, last_seen_ms.

staging_digest = lowercase hex(sha256(compact JSON payload)).

In Go, use a typed struct or another deterministic serializer that preserves the documented field-list order for the digest payload. A generic map[string]any digest payload is not compliant with this contract because json.Marshal emits map keys in alphabetical order rather than the required tenant_id, scenario, schema_hash, operations order.
