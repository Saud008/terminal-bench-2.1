#!/bin/bash
# Staging artifact writer and run ledger persistence.
set -euo pipefail

LEDGER_ROOT="${APP_ROOT:-/app}/state/ledger"

staging_write() {
  local path="$1"
  local run_id="$2"
  local req_hash="$3"
  local catalog_digest="$4"
  shift 4
  local -a unloads=("$@")
  local load_start=$((1 + $#)) 
  # loads and mutations passed via env arrays set by caller
  mkdir -p "$(dirname "${path}")" "${LEDGER_ROOT}"
  local seq=1
  local ledger_file="${LEDGER_ROOT}/${run_id}.ledger"
  if [[ -f "${ledger_file}" ]]; then
    # shellcheck disable=SC1090
    source "${ledger_file}"
    if [[ "${LAST_REQ_HASH:-}" == "${req_hash}" ]]; then
      seq="${LAST_SEQ:-1}"
    else
      seq=$(( ${LAST_SEQ:-0} + 1 ))
    fi
  fi
  {
    echo "schema_version=1"
    echo "run_id=${run_id}"
    echo "request_hash=${req_hash}"
    echo "catalog_digest=${catalog_digest}"
    echo "sequence=${seq}"
    echo "[unloads]"
    printf '%s\n' "${STAGING_UNLOADS[@]}"
    echo "[loads]"
    printf '%s\n' "${STAGING_LOADS[@]}"
    echo "[path_mutations]"
    printf '%s\n' "${STAGING_MUTATIONS[@]}"
    echo "[path_final]"
    printf '%s\n' "${STAGING_PATH_FINAL[@]}"
  } > "${path}"
  cat > "${ledger_file}" <<EOF
LAST_REQ_HASH=${req_hash}
LAST_SEQ=${seq}
EOF
}

request_file_hash() {
  sha256sum "$1" | awk '{print $1}'
}

read_catalog_digest() {
  local snap="$1"
  grep '^catalog_digest=' "${snap}" | head -1 | cut -d= -f2-
}
