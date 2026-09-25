#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
PQGOV_HIDDEN_ROOT=/opt/verifier-fixtures/pqgov python3 /app/fixtures/build_fixtures.py
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/pqgov ./cmd/pqgov
test -x /app/bin/pqgov
echo "go-graphql-persisted-query-cache-governor oracle ready"
