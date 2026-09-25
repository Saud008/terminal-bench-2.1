#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
chmod +x "${APP_ROOT}/bin/tf-tag-sentinel" "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/lib/decoy/"*.sh 2>/dev/null || true
echo "tf-tag-sentinel rebuild ok"
