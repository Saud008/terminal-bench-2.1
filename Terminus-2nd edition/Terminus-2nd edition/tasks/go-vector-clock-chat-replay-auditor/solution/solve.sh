#!/usr/bin/env bash
# Oracle solve — task identity go-vector-clock-chat-replay-auditor token 7717295c
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
VCREPLAY_HIDDEN_ROOT=/opt/verifier-fixtures/vcreplay python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/vcreplay ./cmd/vcreplay
test -x /app/bin/vcreplay
echo "go-vector-clock-chat-replay-auditor oracle ready"
