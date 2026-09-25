#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_LIB="/app/lib/roster"
for f in logparse.py truncate.py commit.py election.py replay.py seal.py ledger.py cli.py; do
  cp "${ROOT_DIR}/files/${f}" "${APP_LIB}/${f}"
done
find "${APP_LIB}" -name '*.py' -exec sed -i 's/\r$//' {} +
bash /app/scripts/verifier-rebuild.sh
echo "rosterctl membership ops oracle ready"
