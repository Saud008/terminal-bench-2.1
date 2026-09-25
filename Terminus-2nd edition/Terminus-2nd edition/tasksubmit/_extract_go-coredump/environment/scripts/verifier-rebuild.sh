#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/coreidx_hidden ]; then
  COREIDX_HIDDEN_ROOT=/opt/verifier-fixtures/coreidx_hidden python3 /app/fixtures/build_fixtures.py
fi
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/coreidx ./cmd/coreidx
