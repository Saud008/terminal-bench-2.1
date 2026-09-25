#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
chmod +x "${APP_ROOT}/scripts/hostsatlas" "${APP_ROOT}/lib/"*.sh 2>/dev/null || true
sed -i 's/\r$//' "${APP_ROOT}/scripts/hostsatlas" "${APP_ROOT}/lib/"*.sh 2>/dev/null || true
install -m 0755 "${APP_ROOT}/scripts/hostsatlas" /usr/local/bin/hostsatlas
echo "hostsatlas rebuilt"
