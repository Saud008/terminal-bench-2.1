#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/filingatlas ]; then
  FILING_HIDDEN_ROOT=/opt/verifier-fixtures/filingatlas python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/filingatlas ./cmd/filingatlas
