# Tensor graph constraint laboratory

Build and extend shapeprop into a new tensor constraint analyzer for ML export pipelines. The working baseline under /app/environment already compiles; your job is to implement the analytical workflow that propagates ONNX-like graph shapes into a JSONL ledger under /app/state and generates a structured constraint diagnostic report at /app/output with deterministic operator violation ordering.

Implement the CLI stages documented in /app/docs/staging_pipeline.md. The new capability must cover transitive dynamic dimension symbols, numpy-style broadcast alignment, initializer binding order, graph input default_shape substitution for dynamic placeholders, batched MatMul rank rules, Reshape negative-one inference, and stable violation sorting for repeated runs.

## Operator workflow

1. Rebuild release shapeprop via /app/environment/scripts/build_all.sh.
2. Run the batch propagation stage on bundled graph JSON, writing the ledger to /app/state/tensor_prop_batch.jsonl
3. Run the violation export stage, writing /app/output/constraint_diagnostic_report.json

## Authoritative contracts

Study these product specs (not this page alone):

- /app/docs/graph_ir_format.md — graph JSON schema and symbol case sensitivity
- /app/docs/dynamic_dim_symbols.md — transitive symbol_links unification
- /app/docs/broadcast_rules.md — right-aligned broadcast for Add and Mul
- /app/docs/initializer_binding.md — initializer declaration order binding
- /app/docs/input_defaults.md — default_shape for -1 placeholders
- /app/docs/operator_shape_rules.md — MatMul, Reshape, Concat, Transpose rules
- /app/docs/diagnostic_contract.md — violation sort order and totals semantics
- /app/docs/hidden_graph_override.md — TB3_GRAPH_DIR alternate graph batch

The metric_trace_decoy module is a non-authoritative decoy and must not participate in propagation or diagnostic export.

Diagnostic output must list violations sorted by node_id then code then tensor, set totals.violation_count to the violations array length, and keep tensor_count aligned with ledger rows per graph_id.

Grading rebuilds the CLI and checks live artifacts; hardcoding ledger or report JSON fails hidden verifier scenarios.
