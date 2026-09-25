#!/usr/bin/env bash
set -euo pipefail
find /app/internal/crpe91 -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/crpe91 -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/scripts/crpe
chmod +x /app/scripts/crpe
