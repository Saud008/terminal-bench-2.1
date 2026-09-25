#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

# Bundled fixture refresh only — verifier-only fixtures are shipped under
# /opt/verifier-fixtures/snapretctl and must not be generated in the agent image.
python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/snapretctl ./cmd/snapretctl
test -x /app/bin/snapretctl
echo "go-csi-volume-snapshot-retention-auditor oracle ready"
