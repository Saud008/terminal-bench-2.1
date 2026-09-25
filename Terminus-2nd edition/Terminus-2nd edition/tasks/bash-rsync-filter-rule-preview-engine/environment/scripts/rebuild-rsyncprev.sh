#!/usr/bin/env bash
set -euo pipefail
find /app/internal/rsfp93 -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/rsfp93 -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/scripts/rsyncprev
chmod +x /app/scripts/rsyncprev
