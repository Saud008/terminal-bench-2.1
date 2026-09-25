#!/usr/bin/env bash
set -euo pipefail
find /app/internal/zfsroll -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/zfsroll -name '*.sh' -exec chmod +x {} +
chmod +x /app/scripts/zfshold /app/scripts/reset-state.sh /app/scripts/rebuild-zfshold.sh
mkdir -p /app/bin /app/state /app/output /app/work
ln -sfn /app/scripts/zfshold /app/bin/zfshold
