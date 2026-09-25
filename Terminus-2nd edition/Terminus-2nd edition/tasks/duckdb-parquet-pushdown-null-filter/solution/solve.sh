#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/files/golden_planner.go" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_planner.go not found under solution/files" >&2
  exit 1
fi

cp -f "${SOL_DIR}/files/golden_planner.go" "${APP}/internal/planner/predicate.go"
cp -f "${SOL_DIR}/files/golden_stats.go" "${APP}/internal/stats/evaluator.go"
cp -f "${SOL_DIR}/files/golden_page.go" "${APP}/internal/page/reader.go"
cp -f "${SOL_DIR}/files/golden_timezone.go" "${APP}/internal/timezone/filter.go"
cp -f "${SOL_DIR}/files/golden_parallel.go" "${APP}/internal/parallel/splitter.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/parquet-pushdown-scan ./cmd/parquet-pushdown-scan

bash "${APP}/scripts/reset-state.sh"
parquet-pushdown-scan filter \
  --catalog /app/fixtures/catalog/06-merged.json \
  --output /app/output/smoke-filter.json \
  --is-null sensor_id \
  --ts-gte 2024-06-15T12:00:00Z \
  --workers 2
