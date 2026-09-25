#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
rm -rf /app/state/* /app/output/* 2>/dev/null || true
mkdir -p /app/state /app/output
: > /app/output/.reset-touch
