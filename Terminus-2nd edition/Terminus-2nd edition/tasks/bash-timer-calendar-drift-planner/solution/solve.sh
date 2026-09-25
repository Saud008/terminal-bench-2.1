#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE_DIR="${SCRIPT_DIR}/files"

install_file() {
  local rel="$1"
  local dest="$2"
  local mode="$3"
  install -m "${mode}" "${ORACLE_DIR}/${rel}" "${APP_ROOT}/${dest}"
  sed -i 's/\r$//' "${APP_ROOT}/${dest}" 2>/dev/null || true
}

install_file lib/common.sh lib/common.sh 0644
install_file lib/units/fragment_merge.py lib/units/fragment_merge.py 0644
install_file lib/calendar/drift_slots.py lib/calendar/drift_slots.py 0644
install_file lib/report/digest_export.py lib/report/digest_export.py 0644

chmod +x "${APP_ROOT}/scripts/systemd-timer-planner.sh" "${APP_ROOT}/scripts/"*.sh
mkdir -p /app/output /app/stage/manifests
