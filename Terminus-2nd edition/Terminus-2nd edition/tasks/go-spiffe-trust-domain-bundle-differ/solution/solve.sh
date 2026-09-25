#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
TDB_HIDDEN_ROOT=/opt/verifier-fixtures/spiffectl python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/spiffectl ./cmd/spiffectl
test -x /app/bin/spiffectl
echo "go-spiffe-trust-domain-bundle-differ oracle ready"
