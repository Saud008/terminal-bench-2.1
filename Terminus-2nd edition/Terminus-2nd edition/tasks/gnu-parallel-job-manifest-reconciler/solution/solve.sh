#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${SCRIPT_DIR}/files"

cp "${PATCHES}/lib/joblog.sh" "${APP_ROOT}/lib/joblog.sh"
cp "${PATCHES}/lib/slots.sh" "${APP_ROOT}/lib/slots.sh"
cp "${PATCHES}/lib/exitagg.sh" "${APP_ROOT}/lib/exitagg.sh"
cp "${PATCHES}/scripts/stage.sh" "${APP_ROOT}/scripts/stage.sh"
cp "${PATCHES}/scripts/export.sh" "${APP_ROOT}/scripts/export.sh"

cd "${APP_ROOT}"
make install
mkdir -p /app/state /app/output
