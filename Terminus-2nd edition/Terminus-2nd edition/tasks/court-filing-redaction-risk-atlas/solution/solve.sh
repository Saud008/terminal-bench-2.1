#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_oracle_patches.sh"

python3 /app/fixtures/build_fixtures.py
FILING_HIDDEN_ROOT=/opt/verifier-fixtures/filingatlas python3 /app/fixtures/build_fixtures.py

go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/filingatlas ./cmd/filingatlas
test -x /app/bin/filingatlas

bash /app/scripts/reset-state.sh
/app/bin/filingatlas load-bundle --scenario party-casefold-match --fixture-dir /app/fixtures >/dev/null
/app/bin/filingatlas index-parties --scenario party-casefold-match >/dev/null
/app/bin/filingatlas scan-risks --scenario party-casefold-match >/dev/null
/app/bin/filingatlas emit-atlas --scenario party-casefold-match >/dev/null
test -s /app/output/redaction-risk-atlas.json

echo "court-filing-redaction-risk-atlas oracle ready"
