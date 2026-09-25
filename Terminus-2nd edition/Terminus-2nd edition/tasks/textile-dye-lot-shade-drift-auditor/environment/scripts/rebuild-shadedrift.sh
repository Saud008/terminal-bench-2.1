#!/usr/bin/env bash
set -euo pipefail
find /app/lib/xk7r -name '*.sh' -exec sed -i 's/\r$//' {} + 
find /app/lib/xk7r -name '*.sh' -exec chmod +x {} +
        chmod +x /app/lib/xk7r/b02/fc02.sh
sed -i 's/\r$//' /app/scripts/shadedrift
chmod +x /app/scripts/shadedrift
