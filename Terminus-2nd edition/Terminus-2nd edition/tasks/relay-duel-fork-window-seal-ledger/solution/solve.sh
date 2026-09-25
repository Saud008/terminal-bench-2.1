#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_LIB="/app/lib/duelctl"
for f in load.py branch.py hold.py terminate.py dedupe.py clock.py window.py sqlite_pub.py; do
  cp "${ROOT_DIR}/files/${f}" "${APP_LIB}/${f}"
done
find "${APP_LIB}" -name '*.py' -exec sed -i 's/\r$//' {} +
bash /app/scripts/rebuild-duelctl.sh
echo "relay-duel-fork-window-seal-ledger oracle ready"
