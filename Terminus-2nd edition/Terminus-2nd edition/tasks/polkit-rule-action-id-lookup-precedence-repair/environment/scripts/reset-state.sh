#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
rm -rf "${APP_ROOT}/output"/*
mkdir -p "${APP_ROOT}/output" "${APP_ROOT}/state"
echo '{}' > "${APP_ROOT}/state/auth-cache.json"
echo "pkctl state reset"
