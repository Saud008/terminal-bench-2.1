#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -f "${SCRIPT_DIR}/golden_header.go" "${APP_ROOT}/internal/frame/header.go"
cp -f "${SCRIPT_DIR}/golden_fsm.go" "${APP_ROOT}/internal/surveyor/fsm.go"
cp -f "${SCRIPT_DIR}/golden_merge.go" "${APP_ROOT}/internal/ballot/merge.go"
cp -f "${SCRIPT_DIR}/golden_session.go" "${APP_ROOT}/internal/ttl/session.go"
cp -f "${SCRIPT_DIR}/golden_dedup.go" "${APP_ROOT}/internal/topology/dedup.go"
cp -f "${SCRIPT_DIR}/golden_publish.go" "${APP_ROOT}/internal/export/publish.go"
cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/ballotmesh ./cmd/ballotmesh
bash "${APP_ROOT}/scripts/reset-state.sh"
