# Zap Segment Format

Segments are stored as JSON files under the per-index segments directory beneath /app/state/indexes (or under TB3_INDEX_PREFIX when set).

Segment file schema:
- segment_id: integer
- records: array of record objects

Record object schema:
- doc_id: integer
- id: string
- key: string
- payload: string
- checksum: integer

## Checksum contract

Checksum verification uses **FNV-1 64-bit** (not FNV-1a) over the UTF-8 bytes of the exact string `{id}:{key}:{payload}`.

FNV-1 update order for each input byte `b`:
1. multiply the running hash by the FNV prime `1099511628211` (wrapping mod 2^64)
2. xor the running hash with `b`

Offset basis is `14695981039346656037`.

FNV-1a (xor then multiply) is a different algorithm and must not be used for segment admission. Optional decoy helpers under `src/decoy/` are not on the ingest/export hot path and must not redefine this contract.
