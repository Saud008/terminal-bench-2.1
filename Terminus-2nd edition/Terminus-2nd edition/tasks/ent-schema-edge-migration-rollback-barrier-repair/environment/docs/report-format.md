# Migration report format

Output path default: /app/output/migration-report.json

Fields:

- schema_version integer — 3 after successful up, 2 after full down.
- codegen_hash string — eight-byte hex from codegen refresh, never ent-codegen-v2-stale after fix.
- snapshot_seq integer — positive table count at snapshot.
- events array of objects with phase string and seq integer ascending. First event must be codegen_refresh before atlas_snapshot on up.
- counts object with posts integer and orphans integer (orphans zero after up).
- direction string up or down.
- seed string when provided on up.

Phase names match migration-pipeline.md: codegen_refresh, atlas_snapshot, ent_pre_validate, add_author_nullable, backfill_author, ent_post_validate, set_author_not_null, add_post_author_fk, add_author_index.
