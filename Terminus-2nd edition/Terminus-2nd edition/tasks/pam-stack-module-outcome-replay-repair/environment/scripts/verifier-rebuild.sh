#!/usr/bin/env bash
set -euo pipefail

cd /app

sed -i 's/\r$//' /app/bin/pamreplay /app/scripts/*.sh /app/lib/*.sh /app/stubs/*.sh 2>/dev/null || true
chmod +x /app/bin/pamreplay /app/scripts/*.sh /app/lib/*.sh /app/stubs/*.sh 2>/dev/null || true

bash /app/scripts/reset-state.sh
