#!/usr/bin/env bash
set -euo pipefail
find /app/internal/pk87 -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/pk87 -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/bin/gclint
chmod +x /app/bin/gclint
