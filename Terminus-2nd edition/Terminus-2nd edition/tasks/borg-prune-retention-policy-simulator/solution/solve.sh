#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${SCRIPT_DIR}/files"

cp "${PATCHES}/lib/common.sh" "${APP_ROOT}/lib/common.sh"
cp "${PATCHES}/lib/parse_list.sh" "${APP_ROOT}/lib/parse_list.sh"
cp "${PATCHES}/lib/clock_skew.sh" "${APP_ROOT}/lib/clock_skew.sh"
cp "${PATCHES}/lib/holds.sh" "${APP_ROOT}/lib/holds.sh"
cp "${PATCHES}/lib/retention.sh" "${APP_ROOT}/lib/retention.sh"
cp "${PATCHES}/lib/staging/io.sh" "${APP_ROOT}/lib/staging/io.sh"
cp "${PATCHES}/scripts/export.sh" "${APP_ROOT}/scripts/export.sh"

cd "${APP_ROOT}"
make install
mkdir -p /app/output /app/state
