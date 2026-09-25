# Ingest and export pipeline

## Ingest

```
avsccompat ingest --schema-dir <DIR> --pairs <PAIRS.jsonl> --staging /app/state/schema_pair_ledger.jsonl
```

Each pairs line is JSON with subject, writer, and reader paths relative to schema-dir.

Staging lines are JSON objects sorted by **subject** ascending. Each line includes writer_fingerprint, reader_fingerprint, compatible flag, violations list, and checks object with namespace_alias_ok, defaults_ok, union_order_ok, and logical_types_ok booleans.

## Export

```
avsccompat export --staging /app/state/schema_pair_ledger.jsonl --out /app/output/avro_migration_report.json
```

Export reads staging and writes subjects sorted by subject name with risk_level and totals.pair_count equal to the number of pairs evaluated.

Compatible pairs must export risk_level low. Logical type failures must be critical.
