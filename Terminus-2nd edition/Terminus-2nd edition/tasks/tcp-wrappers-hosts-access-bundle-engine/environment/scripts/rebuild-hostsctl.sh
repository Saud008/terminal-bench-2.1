#!/usr/bin/env bash
set -euo pipefail

cd /app

sed -i 's/\r$//' /app/bin/hostsctl /app/scripts/*.sh /app/lib/*.sh 2>/dev/null || true
chmod +x /app/bin/hostsctl /app/scripts/*.sh /app/lib/*.sh 2>/dev/null || true

bash /app/scripts/reset-state.sh
