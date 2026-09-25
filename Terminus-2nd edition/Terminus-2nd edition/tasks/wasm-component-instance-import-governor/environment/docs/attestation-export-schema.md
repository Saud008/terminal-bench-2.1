# Digest-sealed attestation export schema

Sealed publish artifact: /app/output/component-attestation.json is UTF-8 JSON with a top-level components array.

Each element contains:

- name: source filename from the ledger
- imports: array of objects with module, name, and type_index fields in canonical tuple order
- surface_exports: array of objects with outer name and resolved_leaf fields after transitive closure
- import_reorder_digest: lowercase hex SHA-256 over canonical import bytes defined in attestation-digest.md

The ingest_seq field at the top level mirrors the ledger ingest sequence.
