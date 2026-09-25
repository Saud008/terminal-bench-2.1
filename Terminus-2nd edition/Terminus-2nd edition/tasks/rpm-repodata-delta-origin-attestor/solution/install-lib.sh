#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LIB=/app/lib
install -m 755 "${DIR}/patches/repomd.sh" "${LIB}/repomd.sh"
install -m 755 "${DIR}/patches/primary.sh" "${LIB}/primary.sh"
install -m 755 "${DIR}/patches/modules.sh" "${LIB}/modules.sh"
install -m 755 "${DIR}/patches/mirror.sh" "${LIB}/mirror.sh"
install -m 755 "${DIR}/patches/lineage.sh" "${LIB}/lineage.sh"
install -m 755 "${DIR}/patches/export.sh" "${LIB}/export.sh"
