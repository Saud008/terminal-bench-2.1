#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "${SCRIPT_DIR}/golden_cursor.go" "${APP_ROOT}/internal/watch/cursor.go"
cp "${SCRIPT_DIR}/golden_eval.go" "${APP_ROOT}/internal/caveat/eval.go"
cp "${SCRIPT_DIR}/golden_zed.go" "${APP_ROOT}/internal/token/zed.go"
cp "${SCRIPT_DIR}/golden_cache.go" "${APP_ROOT}/internal/closure/cache.go"
cp "${SCRIPT_DIR}/golden_snapshot.go" "${APP_ROOT}/internal/check/snapshot.go"
cp "${SCRIPT_DIR}/golden_stage.go" "${APP_ROOT}/internal/ingest/stage.go"
cp "${SCRIPT_DIR}/golden_publish.go" "${APP_ROOT}/internal/export/publish.go"

export CGO_ENABLED=0
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/relationwatchd ./cmd/relationwatchd

test -x /usr/local/bin/relationwatchd

mkdir -p /app/output /app/state /app/data
