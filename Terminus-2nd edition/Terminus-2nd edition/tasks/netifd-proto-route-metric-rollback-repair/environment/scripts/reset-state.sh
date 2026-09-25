#!/usr/bin/env bash
set -euo pipefail
rm -f /app/output/*.json 2>/dev/null || true
rm -rf /app/state /app/harness/runtime 2>/dev/null || true
mkdir -p /app/output /app/state /app/harness/runtime
: > /app/harness/runtime/teardown.log
