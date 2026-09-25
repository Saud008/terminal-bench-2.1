#!/usr/bin/env bash
set -euo pipefail
pkill -f '/usr/local/bin/grpcfaultd' 2>/dev/null || true
rm -rf /app/output
mkdir -p /app/output
