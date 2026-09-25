#!/usr/bin/env bash
set -euo pipefail
pkill -x kongadmit 2>/dev/null || true
rm -rf /app/work /app/output /app/state
mkdir -p /app/work /app/output /app/state
