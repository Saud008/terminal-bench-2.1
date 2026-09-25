#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
mkdir -p "${APP_ROOT}/output" "${APP_ROOT}/state"
rm -rf "${APP_ROOT}/output/"* "${APP_ROOT}/state/"* 2>/dev/null || true
: > "${APP_ROOT}/state/.reset-marker"
