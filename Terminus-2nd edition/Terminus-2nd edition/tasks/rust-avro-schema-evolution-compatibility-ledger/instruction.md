# Avro schema evolution compatibility ledger

Implement an Avro schema evolution compatibility ledger for the streaming platform under /app. Producer and consumer schema pairs are evaluated for reader-writer compatibility, staged as JSONL rows, and summarized in a migration risk export.

Ingest must write `/app/state/schema_pair_ledger.jsonl`. Export must produce `/app/output/avro_migration_report.json`. Namespace aliasing, default rules, union branch ordering, logical types, and parsing fingerprints follow the cited docs.

The release `avsccompat` binary under `/app/environment` must support ingest (schema directory + pairs file to staging ledger) and export (staging ledger to migration report) with behavior matching `/app/docs/staging_pipeline.md` and the `avro_compat_ref` reference semantics documented there. The evaluator applies Avro reader-writer resolution rules under `/app/docs`, stages compatibility rows, and classifies migration risk on export.

## Contracts

Read and follow:

- /app/docs/avro_compatibility_overview.md
- /app/docs/namespace_aliasing.md
- /app/docs/default_and_union_rules.md
- /app/docs/logical_types_and_fingerprint.md
- /app/docs/staging_pipeline.md (ingest/export command surfaces and avro_compat_ref reference parity)

Required outcomes:

- A release-built `avsccompat` that can ingest the configured schema directory and pairs file into `/app/state/schema_pair_ledger.jsonl`, and export that staging ledger to `/app/output/avro_migration_report.json`.
- Staging rows and export subjects sorted by subject name, with writer/reader fingerprints, `compatible` flags aligned with violations, `risk_level` `low` for compatible pairs, and `totals.pair_count` equal to the evaluated pair count.
- Compatibility and fingerprint fields must match the independent `avro_compat_ref` evaluation of the same schema/pairs inputs (including schema-dir and pairs-file overrides used by grading).

The telemetry_decoy crate under /app/environment is telemetry scaffolding and is not on the ingest or export hot path.

Hardcoding `/app/output/avro_migration_report.json` or editing tests is insufficient. Grading uses subprocess invocations of `avsccompat` after rebuild.
