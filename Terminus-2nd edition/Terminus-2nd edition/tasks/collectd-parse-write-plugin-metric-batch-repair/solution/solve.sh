#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_putval.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_putval.go not found" >&2; exit 1; }

cp -f "${SOL}/golden_putval.go" "${APP}/internal/parse/putval.go"
cp -f "${SOL}/golden_types.go" "${APP}/internal/parse/types.go"
cp -f "${SOL}/golden_escape.go" "${APP}/internal/normalize/escape.go"
cp -f "${SOL}/golden_derive.go" "${APP}/internal/normalize/derive.go"
cp -f "${SOL}/golden_batch.go" "${APP}/internal/flush/batch.go"
cp -f "${SOL}/golden_skew.go" "${APP}/internal/flush/skew.go"
cp -f "${SOL}/golden_staging.go" "${APP}/internal/staging/staging.go"
cp -f "${SOL}/golden_export.go" "${APP}/internal/export/report.go"
cp -f "${SOL}/golden_pipeline.go" "${APP}/internal/pipeline/pipeline.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/collectdctl ./cmd/collectdctl
test -x /usr/local/bin/collectdctl
bash /app/scripts/reset-state.sh
echo "collectdctl oracle ready"
