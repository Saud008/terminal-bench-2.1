#!/usr/bin/env bash
set -euo pipefail
find /app/internal/dirauth -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/dirauth -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/scripts/ldaprm
chmod +x /app/scripts/ldaprm
install -m 0755 /app/scripts/ldaprm /usr/local/bin/ldaprm 2>/dev/null || true
