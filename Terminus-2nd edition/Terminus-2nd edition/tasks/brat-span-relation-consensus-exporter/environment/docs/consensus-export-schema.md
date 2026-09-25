# Consensus export schema

Path: /app/output/consensus-export.json

Fields:

- project_id
- staging_generation
- consensus_generation
- spans: sorted by doc_id, start, end with id, label, score, locked
- relations: sorted by doc_id, arg1_span, arg2_span with type, score, locked
- consensus_digest: sha256: prefix followed by 64 lowercase hex chars

consensus_digest is SHA-256 over compact JSON with sorted keys:

{"project_id":"...","relations":[relation keys sorted],"spans":[span keys sorted]}

Span keys use doc_id:label:start-end. Relation keys use doc_id:arg1_span->arg2_span:type.

export reads consensus-generation.json and staging metadata only. Before sealing, export must reject consensus state when consensus-generation.staging_generation or consensus-generation.project_digest differs from the current staging snapshot.
