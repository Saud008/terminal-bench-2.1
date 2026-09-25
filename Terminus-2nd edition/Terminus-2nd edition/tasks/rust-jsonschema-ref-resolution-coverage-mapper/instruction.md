# JSON Schema ref resolution coverage mapper

Deliver jscovmap under /app/environment for API contract teams who need a canonical map of local JSON Schema reference coverage. The tool traces a schema catalog plus validation example instances into split JSONL staging under /app/state. A separate stage emits the coverage report and reference graph under /app/output.

Behavior is specified only in the cited /app/docs markdown files below. Hidden grading may override schema and example paths through TB3_SCHEMA_DIR and TB3_EXAMPLES_FILE as documented in staging_pipeline.md.

## Pipeline

1. Rebuild the release binary with /app/environment/scripts/build_all.sh.
2. Run trace on the bundled schema directory and validation_examples.jsonl, writing ref_edges.jsonl and example_coverage.jsonl under /app/state
3. Run publish to write schema_coverage_report.json and ref_graph.json under /app/output

## Contracts

Read and follow:

- /app/docs/ref_resolution_overview.md
- /app/docs/anchor_registry.md
- /app/docs/recursive_guard.md
- /app/docs/combinator_coverage.md
- /app/docs/staging_pipeline.md (documents TB3_SCHEMA_DIR and TB3_EXAMPLES_FILE override behavior)
- /app/docs/graph_export.md

The decoy_validate crate is validation scaffolding and is not on the trace or publish hot path.

Hardcoding /app/output artifacts or editing tests is insufficient. Grading uses subprocess invocations of jscovmap after rebuild. Expected outputs are recomputed with the bundled tests/jscov_contract_math.py reference helpers alongside pytest.
