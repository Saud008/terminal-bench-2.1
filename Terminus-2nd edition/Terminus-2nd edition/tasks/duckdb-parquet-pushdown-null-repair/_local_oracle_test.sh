#!/usr/bin/env bash
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
STAGE=/tmp/duckdb-parquet-pushdown-null-repair
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$TASK/environment" "$STAGE/environment"
cp -a "$TASK/tests" "$STAGE/tests"
cp -a "$TASK/solution" "$STAGE/solution"
cd "$STAGE"
docker build -t duckdb-parquet-oracle-test environment/
docker run --rm \
  -v "$STAGE/solution:/solution:ro" \
  -v "$STAGE/tests:/tests:ro" \
  duckdb-parquet-oracle-test \
  bash -c 'bash /solution/solve.sh && bash /tests/test.sh; echo REWARD=$(cat /logs/verifier/reward.txt)'
