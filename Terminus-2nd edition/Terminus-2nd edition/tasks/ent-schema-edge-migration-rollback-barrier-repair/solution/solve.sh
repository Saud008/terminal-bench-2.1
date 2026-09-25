#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${SCRIPT_DIR}/files"

cp "${FILES}/generator.go" "${APP_ROOT}/internal/migrate/generator.go"
cp "${FILES}/applier.go" "${APP_ROOT}/internal/migrate/applier.go"
cp "${FILES}/backfill.go" "${APP_ROOT}/internal/migrate/backfill.go"
cp "${FILES}/refresh.go" "${APP_ROOT}/internal/codegen/refresh.go"

cd "${APP_ROOT}"
bash /app/scripts/verifier-rebuild.sh
test -x /usr/local/bin/entmigrate

mkdir -p /app/output /app/work
bash /app/scripts/reset-state.sh

/usr/local/bin/entmigrate up \
  --catalog /app/fixtures/catalogs/bundled-v3.json \
  --db /app/work/oracle.db \
  --seed bundled \
  --report /app/output/migration-report.json
