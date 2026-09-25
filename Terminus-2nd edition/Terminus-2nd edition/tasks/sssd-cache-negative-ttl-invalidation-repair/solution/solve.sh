#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${SCRIPT_DIR}/patches"

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export GOFLAGS="-mod=vendor"

install -m 0644 "${PATCHES}/cache_key.go" "${APP_ROOT}/internal/cache/key.go"
install -m 0644 "${PATCHES}/cache_negative.go" "${APP_ROOT}/internal/cache/negative.go"
install -m 0644 "${PATCHES}/group_nested.go" "${APP_ROOT}/internal/group/nested.go"
install -m 0644 "${PATCHES}/replay_engine.go" "${APP_ROOT}/internal/replay/engine.go"
install -m 0644 "${PATCHES}/store_sqlite.go" "${APP_ROOT}/internal/store/sqlite.go"
install -m 0644 "${PATCHES}/export_stage.go" "${APP_ROOT}/internal/export/export_stage.go"

cd "${APP_ROOT}"
go build -mod=vendor -o /usr/local/bin/sssdcache ./cmd/sssdcache
test -x /usr/local/bin/sssdcache
bash /app/scripts/reset-state.sh
