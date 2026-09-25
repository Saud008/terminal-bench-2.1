#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
XSNAP_HIDDEN_ROOT=/opt/verifier-fixtures/xsnapctl python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/xsnapctl ./cmd/xsnapctl
test -x /app/bin/xsnapctl
echo "go-envoy-xds-route-snapshot-differ oracle ready"
