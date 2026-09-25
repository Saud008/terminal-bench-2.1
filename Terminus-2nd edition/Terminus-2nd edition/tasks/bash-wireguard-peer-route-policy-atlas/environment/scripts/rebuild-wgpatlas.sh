#!/usr/bin/env bash
set -euo pipefail
find /app/internal/wgpa91 -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/wgpa91 -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' /app/scripts/wgpatlas
chmod +x /app/scripts/wgpatlas
