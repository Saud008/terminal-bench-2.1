#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /app/state /app/work /app/output
export CGO_ENABLED=0
cd /app
bash "${ROOT_DIR}/apply_frontier.sh"
python3 /app/fixtures/build_scenarios.py
if [ -d /opt/verifier-fixtures/overbookctl ]; then
  OVERBOOK_HIDDEN_ROOT=/opt/verifier-fixtures/overbookctl python3 /app/fixtures/build_scenarios.py
fi
test -d /app/cmd/overbookctl
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/overbookctl ./cmd/overbookctl
test -x /app/bin/overbookctl
echo "hotel-overbooking-walk-cost-allocator oracle ready"
