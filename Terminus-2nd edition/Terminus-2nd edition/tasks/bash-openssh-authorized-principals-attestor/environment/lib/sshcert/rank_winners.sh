#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"

order_principal_rows() {
  local input="$1"
  echo "$input" | awk -F'|' 'NF==4 {print}' | LC_ALL=C sort -t'|' -k1,1 -k2,2n -k3,3nr -k4,4
}
