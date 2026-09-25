#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/termsetctl ./cmd/termsetctl
test -x /app/bin/termsetctl
echo "payment-terminal-batch-reversal-settler oracle ready"
