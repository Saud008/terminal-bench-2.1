#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

require_oracle_file() {
  local path="$1"
  if [ ! -f "${path}" ]; then
    echo "oracle bundle missing: ${path}" >&2
    exit 1
  fi
}

assert_non_empty_target() {
  local path="$1"
  if [ ! -s "${path}" ]; then
    echo "oracle install produced empty target: ${path}" >&2
    exit 1
  fi
}

normalize_go_tree() {
  find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
}

normalize_go_tree

require_oracle_file "${FILES_DIR}/oracle_ndc_normalize.go"
cp "${FILES_DIR}/oracle_ndc_normalize.go" /app/internal/formndc/ndc.go
assert_non_empty_target /app/internal/formndc/ndc.go

require_oracle_file "${FILES_DIR}/oracle_preferred_rxnorm.go"
cp "${FILES_DIR}/oracle_preferred_rxnorm.go" /app/internal/formndc/rxnorm.go
assert_non_empty_target /app/internal/formndc/rxnorm.go

require_oracle_file "${FILES_DIR}/oracle_plan_overrides.go"
cp "${FILES_DIR}/oracle_plan_overrides.go" /app/internal/planrule/overrides.go
assert_non_empty_target /app/internal/planrule/overrides.go

require_oracle_file "${FILES_DIR}/oracle_step_therapy.go"
cp "${FILES_DIR}/oracle_step_therapy.go" /app/internal/planrule/steptherapy.go
assert_non_empty_target /app/internal/planrule/steptherapy.go

require_oracle_file "${FILES_DIR}/oracle_effective_dates.go"
cp "${FILES_DIR}/oracle_effective_dates.go" /app/internal/planrule/dates.go
assert_non_empty_target /app/internal/planrule/dates.go

require_oracle_file "${FILES_DIR}/oracle_sqlite_upsert.go"
cp "${FILES_DIR}/oracle_sqlite_upsert.go" /app/internal/store/sqlite.go
assert_non_empty_target /app/internal/store/sqlite.go

require_oracle_file "${FILES_DIR}/oracle_matrix_publish.go"
cp "${FILES_DIR}/oracle_matrix_publish.go" /app/internal/matrixout/matrix.go
assert_non_empty_target /app/internal/matrixout/matrix.go

require_oracle_file "${FILES_DIR}/oracle_roster_write.go"
cp "${FILES_DIR}/oracle_roster_write.go" /app/internal/rosterfreeze/disk.go
assert_non_empty_target /app/internal/rosterfreeze/disk.go

require_oracle_file "${FILES_DIR}/oracle_refresh_engine.go"
cp "${FILES_DIR}/oracle_refresh_engine.go" /app/internal/refreshpass/core.go
assert_non_empty_target /app/internal/refreshpass/core.go

if ! grep -q 'RefreshRevision = gen.RefreshRevision + 1' /app/internal/refreshpass/core.go; then
  sed -i 's/gen.RefreshRevision = gen.RefreshRevision$/gen.RefreshRevision = gen.RefreshRevision + 1/' \
    /app/internal/refreshpass/core.go
fi

if ! grep -q 'RefreshRevision + 1' /app/internal/refreshpass/core.go; then
  echo "refresh revision counter patch missing" >&2
  exit 1
fi
