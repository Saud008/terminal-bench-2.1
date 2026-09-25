#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_scenarios.py
if [ -d /opt/verifier-fixtures/venuetixctl ]; then
  VENUETIX_HIDDEN_ROOT=/opt/verifier-fixtures/venuetixctl python3 /app/fixtures/build_scenarios.py
fi
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/venuetixctl ./cmd/venuetixctl
