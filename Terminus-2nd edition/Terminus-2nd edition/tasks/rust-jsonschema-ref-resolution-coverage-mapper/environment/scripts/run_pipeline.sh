#!/usr/bin/env bash
set -euo pipefail
/app/environment/scripts/build_all.sh
mkdir -p /app/state /app/output
SCHEMA_DIR="${TB3_SCHEMA_DIR:-/app/environment/fixtures/schemas}"
EXAMPLES="${TB3_EXAMPLES_FILE:-/app/environment/fixtures/validation_examples.jsonl}"
/app/environment/tools/jscovmap/jscovmap trace \
  --schema-dir "$SCHEMA_DIR" \
  --examples "$EXAMPLES" \
  --ref-edges /app/state/ref_edges.jsonl \
  --coverage /app/state/example_coverage.jsonl
/app/environment/tools/jscovmap/jscovmap publish \
  --ref-edges /app/state/ref_edges.jsonl \
  --coverage /app/state/example_coverage.jsonl \
  --report /app/output/schema_coverage_report.json \
  --graph /app/output/ref_graph.json
