#!/usr/bin/env bash
set -euo pipefail
APP="/app"
find "$APP/lib/attpipe" -name '*.sh' -exec sed -i 's/\r$//' {} +
find "$APP/lib/attpipe" -name '*.sh' -exec chmod +x {} +
sed -i 's/\r$//' "$APP/scripts/kcfgattest" "$APP/scripts/reset-state.sh" "$APP/scripts/rebuild-kcfgattest.sh"
chmod +x "$APP/scripts/kcfgattest" "$APP/scripts/reset-state.sh" "$APP/scripts/rebuild-kcfgattest.sh"
echo "kcfgattest modules synced"
