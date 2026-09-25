#!/usr/bin/env bash
set -euo pipefail
cd /app
find /app/scripts /app/lib/sled -type f \( -name '*.sh' -o -name 'sledtool' -o -name '*.py' \) -exec sed -i 's/\r$//' {} + 2>/dev/null || true
chmod +x /app/scripts/sledtool /app/bin/sledtool 2>/dev/null || true
install -m 0755 /app/scripts/sledtool /usr/local/bin/sledtool
