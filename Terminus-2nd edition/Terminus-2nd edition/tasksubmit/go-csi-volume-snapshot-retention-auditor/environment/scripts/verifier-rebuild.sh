#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/snapretctl ]; then
  SNAPRET_HIDDEN_ROOT=/opt/verifier-fixtures/snapretctl python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/snapretctl ./cmd/snapretctl
