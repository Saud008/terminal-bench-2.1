#!/usr/bin/env bash
set -euo pipefail
chmod +x /app/tools/udev-policy-planner /app/lib/cli.sh
find /app/lib -name '*.sh' -exec chmod +x {} \;
mkdir -p /app/bin /app/state /app/output
ln -sf /app/tools/udev-policy-planner /app/bin/udev-policy-planner
echo "rebuild-udevplan: ok"
