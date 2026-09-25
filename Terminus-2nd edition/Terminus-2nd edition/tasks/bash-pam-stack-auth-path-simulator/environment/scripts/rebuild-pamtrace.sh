#!/usr/bin/env bash
set -euo pipefail
find /app/internal/pamcore -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/pamcore -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/scripts/pamtrace
chmod +x /app/scripts/pamtrace
