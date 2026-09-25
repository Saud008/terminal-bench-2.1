#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_registry_scenarios.py
if [ -d /opt/verifier-fixtures/intakectl ]; then
  ASIQ_HIDDEN_ROOT=/opt/verifier-fixtures/intakectl python3 /app/fixtures/build_registry_scenarios.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/intakectl ./cmd/intakectl
