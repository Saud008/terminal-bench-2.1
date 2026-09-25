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

require_oracle_file "${FILES_DIR}/oracle_claim_bind.go"
cp "${FILES_DIR}/oracle_claim_bind.go" /app/internal/claimlnk/bind.go
assert_non_empty_target /app/internal/claimlnk/bind.go

require_oracle_file "${FILES_DIR}/oracle_sc_days.go"
cp "${FILES_DIR}/oracle_sc_days.go" /app/internal/scdays/scdays.go
assert_non_empty_target /app/internal/scdays/scdays.go

require_oracle_file "${FILES_DIR}/oracle_orph_probe.go"
cp "${FILES_DIR}/oracle_orph_probe.go" /app/internal/orphscan/probe.go
assert_non_empty_target /app/internal/orphscan/probe.go

require_oracle_file "${FILES_DIR}/oracle_bp_rank.go"
cp "${FILES_DIR}/oracle_bp_rank.go" /app/internal/bprank/rank.go
assert_non_empty_target /app/internal/bprank/rank.go

require_oracle_file "${FILES_DIR}/oracle_ns_rollup.go"
cp "${FILES_DIR}/oracle_ns_rollup.go" /app/internal/nsbkt/rollup.go
assert_non_empty_target /app/internal/nsbkt/rollup.go

require_oracle_file "${FILES_DIR}/oracle_vol_emit.go"
cp "${FILES_DIR}/oracle_vol_emit.go" /app/internal/volrep/emit.go
assert_non_empty_target /app/internal/volrep/emit.go

require_oracle_file "${FILES_DIR}/oracle_flt_persist.go"
cp "${FILES_DIR}/oracle_flt_persist.go" /app/internal/fltstore/persist.go
assert_non_empty_target /app/internal/fltstore/persist.go

if ! grep -q 'AuditPassSeq = gen.AuditPassSeq + 1' /app/internal/analyzepass/core.go; then
  sed -i 's/gen.AuditPassSeq = gen.AuditPassSeq$/gen.AuditPassSeq = gen.AuditPassSeq + 1/' \
    /app/internal/analyzepass/core.go
fi

if ! grep -q 'AuditPassSeq + 1' /app/internal/analyzepass/core.go; then
  echo "analyze pass counter patch missing" >&2
  exit 1
fi
