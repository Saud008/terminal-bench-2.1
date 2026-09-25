#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
OUTPUT_DIR="${APP_ROOT}/output"
rm -rf "${STATE_DIR}" "${OUTPUT_DIR}"
mkdir -p "${STATE_DIR}" "${OUTPUT_DIR}"
echo '{"run_seq":0,"last_bundle_fingerprint":"","bundle_id":""}' > "${STATE_DIR}/run-seq.json"
