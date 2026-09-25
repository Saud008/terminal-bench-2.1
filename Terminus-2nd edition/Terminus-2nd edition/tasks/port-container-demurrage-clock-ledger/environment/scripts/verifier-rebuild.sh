#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/demurctl ]; then
  DEMUR_HIDDEN_ROOT=/opt/verifier-fixtures/demurctl python3 /app/fixtures/build_fixtures.py
fi
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/demurctl ./cmd/demurctl
