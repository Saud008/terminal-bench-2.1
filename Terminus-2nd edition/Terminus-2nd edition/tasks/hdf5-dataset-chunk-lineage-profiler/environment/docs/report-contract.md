# Report emission contract

## State snapshot (/app/state/staging.json)

JSON object fields:

- version: 1
- catalog_root: from catalog
- sequence: monotonic ingest counter persisted in /app/state/sequence.txt (starts at 1)
- chunks: array of chunk records
- compression_totals: aggregate payload, masked cells, filter_usage map

Each chunk record must include filter_chain_hash (non-empty) matching filter-chain.md.

## Lineage report (/app/output/lineage_report.json)

Top-level fields: version, sequence, datasets, compression_summary, export_fingerprint.

## Persisted state paths

Ingest writes /app/state/staging.json and maintains the monotonic counter at /app/state/sequence.txt.

Export reads /app/state/staging.json and writes /app/output/lineage_report.json.

datasets is a map keyed by dataset path. Each value lists chunks sorted ascending by chunk_index, attribute_lineage, coordinate_ok, chunk_count.

Stable export rules:

- Serialize with serde_json::to_string on the full report value (compact, no pretty spaces).
- Append exactly one trailing newline.
- export_fingerprint is SHA-256 hex of the compact JSON encoding of the datasets map only (before wrapping in the full report object).
- Repeated export without changing staging must yield byte-identical output files.

## Environment overrides for tests

When TB3_BUNDLE is set, ingest reads that directory instead of the --catalog argument path for catalog/index/mask loading only (state path unchanged). The default hidden bundle directory is /opt/verifier-fixtures/tb3_shadow.

When TB3_STATE_ROOT is set, export reads staging from that directory instead of --state.
