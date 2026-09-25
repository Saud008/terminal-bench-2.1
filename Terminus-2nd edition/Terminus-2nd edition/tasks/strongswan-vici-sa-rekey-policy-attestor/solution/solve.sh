#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -f "${SCRIPT_DIR}/files/golden_rekey.go" "${APP_ROOT}/internal/fsm/rekey.go"
cp -f "${SCRIPT_DIR}/files/golden_selectors.go" "${APP_ROOT}/internal/childsa/selectors.go"
cp -f "${SCRIPT_DIR}/files/golden_uidmap.go" "${APP_ROOT}/internal/ikesa/uidmap.go"
cp -f "${SCRIPT_DIR}/files/golden_log.go" "${APP_ROOT}/internal/sequence/log.go"
cp -f "${SCRIPT_DIR}/files/golden_publish.go" "${APP_ROOT}/internal/export/publish.go"
cp -f "${SCRIPT_DIR}/files/golden_engine.go" "${APP_ROOT}/internal/replay/engine.go"
cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/vicireplay ./cmd/vicireplay
bash "${APP_ROOT}/scripts/reset-state.sh"
