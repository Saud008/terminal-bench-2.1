#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh
test -x /app/bin/snapretctl
echo "go-csi-volume-snapshot-retention-auditor oracle ready"
