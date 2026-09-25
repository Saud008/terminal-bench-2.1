# Avro schema evolution compatibility overview

The avsccompat tool validates whether a reader schema can decode data written with a writer schema. Each producer/consumer pair is evaluated for namespace aliasing, default value rules, union branch compatibility, logical type constraints, and parsing canonical fingerprints.

Compatibility is **reader-centric**: the writer is the on-wire producer schema and the reader is the consumer schema that must decode historical payloads.

## Risk export

After ingest writes /app/state/schema_pair_ledger.jsonl, export produces /app/output/avro_migration_report.json with per-subject risk levels:

- **low** when compatible
- **medium** for single non-logical violations
- **high** for multiple violations
- **critical** when logical type constraints fail

## Verifier fixture override

When TB3_SCHEMA_DIR is set, ingest reads schemas from that directory instead of the bundled registry_inputs/schemas tree. When TB3_PAIRS_FILE is set, ingest uses that pairs file instead of registry_inputs/schema_pairs.jsonl.
