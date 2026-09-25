#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"
python3 /app/fixtures/synthesize_grids.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/gridplan ./cmd/gridplan
test -x /app/bin/gridplan
echo "broadcast-playout-rights-window-planner oracle ready"
