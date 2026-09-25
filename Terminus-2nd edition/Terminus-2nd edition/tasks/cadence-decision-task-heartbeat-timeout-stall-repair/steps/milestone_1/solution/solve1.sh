#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -f "${SCRIPT_DIR}/golden_recorder.go" "${APP_ROOT}/internal/heartbeat/recorder.go"
cp -f "${SCRIPT_DIR}/golden_wheel.go" "${APP_ROOT}/internal/timeout/wheel.go"
cp -f "${SCRIPT_DIR}/golden_reset.go" "${APP_ROOT}/internal/query/reset.go"
cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/cadence-replay ./cmd/cadence-replay
bash "${APP_ROOT}/scripts/reset-state.sh"
