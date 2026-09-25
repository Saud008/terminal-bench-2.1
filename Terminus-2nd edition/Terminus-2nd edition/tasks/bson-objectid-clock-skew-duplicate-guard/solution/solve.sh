# Oracle solve — task identity bson-objectid-clock-skew-duplicate-guard token 6d8396ec
#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
APP_ROOT="${APP_ROOT:-/app}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/files" && pwd)"

install -m 0644 "${SOURCE_DIR}/oracle_objclock.go" "${APP_ROOT}/pkg/objclock/generator.go"
install -m 0644 "${SOURCE_DIR}/oracle_digestseal.go" "${APP_ROOT}/pkg/digestseal/snapshot.go"
install -m 0644 "${SOURCE_DIR}/oracle_oidstore.go" "${APP_ROOT}/pkg/oidstore/commit.go"
install -m 0644 "${SOURCE_DIR}/oracle_intakegate.go" "${APP_ROOT}/pkg/intakegate/service.go"
install -m 0644 "${SOURCE_DIR}/oracle_srcursor.go" "${APP_ROOT}/pkg/srcursor/by_path.go"
install -m 0644 "${SOURCE_DIR}/oracle_jsonlresume.go" "${APP_ROOT}/pkg/jsonlresume/apply.go"

cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/wireclock ./cmd/wireclock
bash "${APP_ROOT}/tooling/reset-state.sh"
