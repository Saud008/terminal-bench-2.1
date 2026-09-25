#!/usr/bin/env bash
set -euo pipefail

chmod +x /app/bin/wtstatus-export /app/scripts/*.sh /app/lib/*.sh
sed -i 's/\r$//' /app/bin/wtstatus-export /app/scripts/*.sh /app/lib/*.sh 2>/dev/null || true
