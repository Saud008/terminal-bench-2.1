#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
VCREPLAY_HIDDEN_ROOT=/opt/verifier-fixtures/vcreplay python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/vcreplay ./cmd/vcreplay
