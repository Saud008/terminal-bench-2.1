#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/originctl ./cmd/originctl
