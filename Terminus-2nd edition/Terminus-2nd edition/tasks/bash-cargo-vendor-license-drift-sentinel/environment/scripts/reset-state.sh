#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
rm -rf "${APP_ROOT}/stage/license-compliance" "${APP_ROOT}/state" "${APP_ROOT}/output"
mkdir -p "${APP_ROOT}/stage/license-compliance" "${APP_ROOT}/state" "${APP_ROOT}/output"
echo '{"run_seq":0,"last_workspace_fingerprint":""}' > "${APP_ROOT}/state/run-seq.json"
