#!/usr/bin/env bash
set -euo pipefail
export APP_ROOT="${APP_ROOT:-/app}"
cd "${APP_ROOT}"
rm -f /app/state/capture-staging.json
rm -f /app/state/staging-seq.json
rm -f /app/state/align-generation.json
rm -rf /app/output/*
mkdir -p /app/state /app/output
unset TB3_FIXTURE_DIR
