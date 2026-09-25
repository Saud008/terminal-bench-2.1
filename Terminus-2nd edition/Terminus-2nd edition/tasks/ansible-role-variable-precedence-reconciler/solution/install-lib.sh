#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LIB=/app/lib
install -m 755 "${DIR}/patches/inventory.sh" "${LIB}/inventory.sh"
install -m 755 "${DIR}/patches/role.sh" "${LIB}/role.sh"
install -m 755 "${DIR}/patches/merge.sh" "${LIB}/merge.sh"
install -m 755 "${DIR}/patches/include_vars.sh" "${LIB}/include_vars.sh"
install -m 755 "${DIR}/patches/precedence.sh" "${LIB}/precedence.sh"
