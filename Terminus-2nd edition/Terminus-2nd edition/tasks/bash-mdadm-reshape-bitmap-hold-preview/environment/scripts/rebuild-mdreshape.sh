#!/usr/bin/env bash
set -euo pipefail
find /app/internal/raidops -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/raidops -name '*.sh' -exec chmod +x {} +
chmod +x /app/scripts/mdreshape /app/scripts/reset-state.sh /app/scripts/rebuild-mdreshape.sh
mkdir -p /app/bin /app/state /app/output /app/work
ln -sfn /app/scripts/mdreshape /app/bin/mdreshape
