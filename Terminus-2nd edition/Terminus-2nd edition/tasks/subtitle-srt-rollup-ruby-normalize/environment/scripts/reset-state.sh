#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:${PATH}"
cd /app
mkdir -p /app/output /app/state/srtctl
rm -f /app/output/*.json 2>/dev/null || true
rm -rf /app/state/srtctl/* 2>/dev/null || true
