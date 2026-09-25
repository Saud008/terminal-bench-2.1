#!/usr/bin/env bash
set -euo pipefail
chmod +x /app/sbin/ctrgc /app/lib/cli.sh
find /app/lib -name '*.sh' -exec chmod +x {} \;
mkdir -p /app/bin /app/state /app/output
ln -sf /app/sbin/ctrgc /app/bin/ctrgc
echo "rebuild-ctrgc: ok"
