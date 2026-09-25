#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_LIB="/app/lib/sled"
for f in split.py merge.py underflow.py replay.py checksum.py split_log.py crash_replay.py reclaim.py barrier.py; do
  cp "${ROOT_DIR}/files/${f}" "${APP_LIB}/${f}"
done
find "${APP_LIB}" -name '*.py' -exec sed -i 's/\r$//' {} +
bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh
echo "sledtool pagestore ops oracle ready"
