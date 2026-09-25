#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"

enforce_wildcard_policy() {
  principal_wildcard_bad "$1" && return 1
  return 0
}
