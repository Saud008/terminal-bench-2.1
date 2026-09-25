#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/chmutled ./cmd/chmutled
