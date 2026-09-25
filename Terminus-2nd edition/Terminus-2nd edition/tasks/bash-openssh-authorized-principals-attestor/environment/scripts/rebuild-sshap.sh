#!/usr/bin/env bash
set -euo pipefail
chmod +x /app/scripts/sshap /app/lib/**/*.sh /app/lib/**/**/*.sh 2>/dev/null || true
find /app/lib -name '*.sh' -exec chmod +x {} +
chmod +x /app/scripts/sshap /app/scripts/*.sh
install -m 0755 /app/scripts/sshap /usr/local/bin/sshap 2>/dev/null || true
