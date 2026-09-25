#!/usr/bin/env bash
set -euo pipefail

find /app/lib -name '*.sh' -exec chmod +x {} +
chmod +x /app/bin/walplan /app/scripts/*.sh
