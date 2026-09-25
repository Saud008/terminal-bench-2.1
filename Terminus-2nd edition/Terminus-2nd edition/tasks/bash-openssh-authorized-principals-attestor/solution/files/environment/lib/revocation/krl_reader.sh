#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"

read_krl_revocations() {
  local krl="$1"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^# ]] && continue
    [[ "$line" =~ ^fingerprint ]] || continue
    echo "$line" | awk '{print tolower($2)}'
  done < "$krl"
}
