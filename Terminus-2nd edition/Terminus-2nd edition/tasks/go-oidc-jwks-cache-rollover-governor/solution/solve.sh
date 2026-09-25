#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

. "${ROOT_DIR}/install_jwks_governor_modules.sh"

/usr/bin/python3 /app/fixtures/build_fixtures.py
OIDC_HIDDEN_ROOT=/opt/verifier-fixtures/oidcgov /usr/bin/python3 /app/fixtures/build_fixtures.py
/usr/local/go/bin/go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/oidcgov ./cmd/oidcgov
/usr/bin/test -x /app/bin/oidcgov
echo "go-oidc-jwks-cache-rollover-governor oracle ready"
