# Staging pipeline

Ingest walks graphs, propagates shapes, and writes the ledger at /app/state/tensor_prop_batch.jsonl. Rows must appear in ascending ordinal order within each graph. Audit reads staging plus the same graph directory to emit the report at /app/output/constraint_diagnostic_report.json

Each ledger row includes a node_id string. Graph inputs use the exact value `input`. Initializers use the exact value `initializer`. Operator outputs use the producing node's `id` from the graph document.
