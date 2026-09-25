#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/qqraftctl ]; then
  QQRAFT_HIDDEN_ROOT=/opt/verifier-fixtures/qqraftctl python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/qqraftctl ./cmd/qqraftctl
