#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_scenarios.py
if [ -d /opt/verifier-fixtures/overbookctl ]; then
  OVERBOOK_HIDDEN_ROOT=/opt/verifier-fixtures/overbookctl python3 /app/fixtures/build_scenarios.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/overbookctl ./cmd/overbookctl
