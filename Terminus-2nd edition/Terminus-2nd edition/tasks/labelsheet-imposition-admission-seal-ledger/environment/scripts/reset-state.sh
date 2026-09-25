#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${SHEET_APP_ROOT:-/app}"
rm -rf "${APP_ROOT}/fixtures/catalog.json" "${APP_ROOT}/fixtures/seeds.json" "${APP_ROOT}/fixtures/marks"
mkdir -p "${APP_ROOT}/fixtures"
cp -a /opt/verifier-fixtures/. "${APP_ROOT}/fixtures/"
rm -f "${APP_ROOT}/output/"*.png "${APP_ROOT}/output/"*.json 2>/dev/null || true
mkdir -p "${APP_ROOT}/output"
