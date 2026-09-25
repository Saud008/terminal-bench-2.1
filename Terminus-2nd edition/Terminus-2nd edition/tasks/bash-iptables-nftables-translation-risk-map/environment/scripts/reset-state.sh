#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
mkdir -p "${APP_ROOT}/state" "${APP_ROOT}/output"
rm -f "${APP_ROOT}/state"/*
echo '{"run_seq":0,"last_pair_fingerprint":"","pair_id":""}' > "${APP_ROOT}/state/run-seq.json"
: > "${APP_ROOT}/state/active-pair.id"
