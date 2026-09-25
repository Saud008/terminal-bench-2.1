#!/usr/bin/env bash
set -euo pipefail
find /app/lib -name '*.sh' -exec chmod +x {} +
chmod +x /app/scripts/bondattest /app/scripts/*.sh
install -m 0755 /app/scripts/bondattest /usr/local/bin/bondattest 2>/dev/null || true
