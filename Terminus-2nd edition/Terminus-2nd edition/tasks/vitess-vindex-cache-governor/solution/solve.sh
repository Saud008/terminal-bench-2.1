#!/usr/bin/env bash
set -euo pipefail

APP="/app"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXED="${SCRIPT_DIR}/fixed"
[[ -d "${FIXED}" ]] || FIXED="/solution/fixed"

cp -f "${FIXED}/hasher.go" "${APP}/internal/vindex/hasher.go"
cp -f "${FIXED}/lookup.go" "${APP}/internal/cache/lookup.go"
cp -f "${FIXED}/scatter.go" "${APP}/internal/planner/scatter.go"
cp -f "${FIXED}/hook.go" "${APP}/internal/migration/hook.go"
cp -f "${FIXED}/ingest.go" "${APP}/internal/ingest/stage.go"

cd "${APP}"
go build -mod=readonly -o /usr/local/bin/vtgatesim ./cmd/vtgatesim
bash /app/scripts/reset-state.sh
echo "vtgatesim oracle ready"
