#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export GOCACHE="${GOCACHE:-/home/agent/.cache/go-build}"
mkdir -p "${GOCACHE}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/iceexpctl ] && [ -w /opt/verifier-fixtures/iceexpctl ]; then
  ICEEXP_HIDDEN_ROOT=/opt/verifier-fixtures/iceexpctl python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/iceexpctl ./cmd/iceexpctl
test -x /app/bin/iceexpctl
echo "go-iceberg-manifest-snapshot-expiry-curator oracle ready"
