#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/oidcgov ]; then
  OIDC_HIDDEN_ROOT=/opt/verifier-fixtures/oidcgov python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/oidcgov ./cmd/oidcgov
