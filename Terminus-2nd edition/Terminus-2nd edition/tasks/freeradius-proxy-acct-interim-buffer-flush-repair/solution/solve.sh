#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${SCRIPT_DIR}"

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export GOFLAGS="-mod=vendor"

cp "${PATCHES}/golden_interval.go" "${APP_ROOT}/internal/attribute/interval.go"
cp "${PATCHES}/golden_dedupe.go" "${APP_ROOT}/internal/session/dedupe.go"
cp "${PATCHES}/golden_queue.go" "${APP_ROOT}/internal/proxy/queue.go"
cp "${PATCHES}/golden_sqlite.go" "${APP_ROOT}/internal/store/sqlite.go"
cp "${PATCHES}/golden_stage.go" "${APP_ROOT}/internal/export/stage.go"

cd "${APP_ROOT}"
go build -mod=vendor -o /usr/local/bin/radiusproxy ./cmd/radiusproxy
test -x /usr/local/bin/radiusproxy
bash /app/scripts/reset-state.sh
