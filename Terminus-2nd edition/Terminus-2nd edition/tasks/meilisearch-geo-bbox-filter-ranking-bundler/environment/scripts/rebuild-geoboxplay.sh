#!/usr/bin/env bash
set -euo pipefail
find /app/internal/mbx7 -name '*.sh' -exec sed -i 's/\r$//' {} +
find /app/internal/mbx7 -name '*.sh' -exec chmod +x {} +
chmod +x /app/scripts/geoboxplay /app/scripts/reset-state.sh /app/scripts/rebuild-geoboxplay.sh
mkdir -p /app/bin /app/state /app/output /app/work
ln -sfn /app/scripts/geoboxplay /app/bin/geoboxplay
ln -sfn /app/scripts/rebuild-geoboxplay.sh /app/bin/rebuild-geoboxplay.sh
