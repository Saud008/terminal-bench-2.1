#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/bondacc ]; then
  TB3_FIXTURE_DIR=/opt/verifier-fixtures/bondacc python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/bondacc ./cmd/bondacc
