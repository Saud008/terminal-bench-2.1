#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
rm -rf /app/output
mkdir -p /app/output
riverbench reset --config /app/config/scheduler.json 2>/dev/null || true
