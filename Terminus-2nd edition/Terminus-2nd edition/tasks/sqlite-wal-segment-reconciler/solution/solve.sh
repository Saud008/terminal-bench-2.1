#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLAY="${SCRIPT_DIR}/patches"

install -m 644 "${OVERLAY}/wal-common.sh" "${APP_ROOT}/lib/common.sh"
install -m 644 "${OVERLAY}/wal-header.sh" "${APP_ROOT}/lib/header.sh"
install -m 644 "${OVERLAY}/wal-frames.sh" "${APP_ROOT}/lib/frames.sh"
install -m 755 "${OVERLAY}/wal-reconcile.sh" "${APP_ROOT}/scripts/reconcile.sh"
install -m 755 "${OVERLAY}/wal-stage.sh" "${APP_ROOT}/scripts/stage.sh"
install -m 755 "${OVERLAY}/wal-export.sh" "${APP_ROOT}/scripts/export.sh"

cd "${APP_ROOT}"
make install
mkdir -p /app/state /app/output
