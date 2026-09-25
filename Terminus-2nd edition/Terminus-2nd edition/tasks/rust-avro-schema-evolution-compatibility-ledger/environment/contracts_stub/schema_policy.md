# Schema policy contract stubs

Violation tags used in staging rows and export risk classification:

- namespace_alias
- default_rules
- union_order
- logical_types

Risk levels emitted on export:

- low for compatible pairs
- medium for single-violation incompatible pairs
- high for multi-violation incompatible pairs
- critical when logical_types appears in violations

Staging checks object keys:

- namespace_alias_ok
- defaults_ok
- union_order_ok
- logical_types_ok

Report paths:

- /app/state/schema_pair_ledger.jsonl
- /app/state/probe_staging.jsonl
- /app/output/avro_migration_report.json
- /app/output/probe_report.json
- /app/catalog/schemas
- /app/catalog/schema_pairs.jsonl

Sample bundled subjects include User, Payment, and Order pairs in the default catalog.

Hidden probe override environment variables:

- TB3_SCHEMA_DIR
- TB3_PAIRS_FILE

The decoy_metrics wrap_schema_bytes helper must never appear in export JSON.
