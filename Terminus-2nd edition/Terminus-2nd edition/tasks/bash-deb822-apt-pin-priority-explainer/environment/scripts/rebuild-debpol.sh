#!/usr/bin/env bash
set -euo pipefail
find /app/lib/pq7m -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/lib/pq7m -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/scripts/debpol
chmod +x /app/scripts/debpol
