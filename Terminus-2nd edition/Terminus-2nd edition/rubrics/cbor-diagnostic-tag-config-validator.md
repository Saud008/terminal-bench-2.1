# Platform rubric — cbor-diagnostic-tag-config-validator

**Task folder:** tasks/cbor-diagnostic-tag-config-validator/

# Rubric 1

Agent uses 0x58 length prefix with exact inner CBOR length for tag 24 envelopes, +3
Agent wraps policy maps as definite-length byte strings under diagnostic tag 24, +3
Agent stages beta long-policy bundles with correct tag-24 wire encoding, +3
Agent decodes tag 24 envelope extracting policy and nonce fields, +2
Agent leaves saturating_sub(1) length prefix in wrap_tag24 so tag-24 length stays wrong, -3

# Rubric 2

Agent places version as first key in staged CBOR map per signing order, +3
Agent preserves diagnostic_tags array element order from ingest, +3
Agent emits staging map without lexicographic key sorting, +3
Agent includes envelope as the fourth map entry after diagnostic_tags, +2
Agent keeps lexicographic sort on staging map keys, -3

# Rubric 3

Agent validates bundle_id policy and nonce before writing staging.cbor, +3
Agent skips staging file creation when ingest validation fails, +3
Agent returns non-zero exit on invalid empty policy ingest bundles, +2
Agent creates /app/state parent directories only before successful staging write, +3
Agent writes staging.cbor before validation so failed ingest still leaves staging file, -3

# Rubric 4

Agent computes staged_digest as SHA-256 over canonical staging bytes, +3
Agent signs attestation HMAC over canonical staging byte sequence not on-disk file, +3
Agent ignores --ingest-source for signature input while still exporting attestation, +3
Agent writes attestation JSON with audit_row_count and diagnostic_tag_summary fields, +2
Agent keeps ingest-source branch feeding on-disk bytes into HMAC instead of canonical staging bytes, -3

# Rubric 5

Agent inserts first ingest audit row with action ingest per bundle, +3
Agent uses INSERT OR IGNORE with bundle_id and nonce uniqueness, +3
Agent keeps audit_row_count at one after --revalidate on unchanged bundle, +3
Agent creates unique index on bundle_id and nonce pairs for idempotent ingest, +2
Agent uses plain INSERT so revalidation keeps incrementing audit row count, -3
