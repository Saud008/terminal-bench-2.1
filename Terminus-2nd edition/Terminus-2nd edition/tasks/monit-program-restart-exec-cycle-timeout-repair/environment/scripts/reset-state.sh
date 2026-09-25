#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${MONIT_APP_ROOT:-/app}"
export MONIT_APP_ROOT="${APP_ROOT}"
mkdir -p "${APP_ROOT}/output" "${APP_ROOT}/state" "${APP_ROOT}/work"
rm -f "${APP_ROOT}/state/cycle-snapshot.json" "${APP_ROOT}/state/cycle-counter.state" \
  "${APP_ROOT}/state/notify.log" "${APP_ROOT}/work/"*.pid
find "${APP_ROOT}/state" -maxdepth 1 -name 'monit-*.id' -delete 2>/dev/null || true
find "${APP_ROOT}/state" -maxdepth 1 -name 'monit-*.id.order' -delete 2>/dev/null || true
: > "${APP_ROOT}/state/notify.log"
