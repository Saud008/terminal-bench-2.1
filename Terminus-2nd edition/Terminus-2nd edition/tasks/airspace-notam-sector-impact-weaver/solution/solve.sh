#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

. "${ROOT_DIR}/install_airclos_lemmas.sh"

/usr/bin/python3 /app/fixtures/build_fixtures.py
AIRCLOS_HIDDEN_ROOT=/opt/verifier-fixtures/airclos /usr/bin/python3 /app/fixtures/build_fixtures.py
/usr/local/go/bin/go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/airclos ./cmd/airclos
/usr/bin/test -x /app/bin/airclos
echo "airclos closure-lab oracle ready"
