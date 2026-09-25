# Oracle solve - task identity go-kafka-compacted-topic-snapshot-curator token 3c5e9012
#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/apply_frontier.sh"

python3 /app/fixtures/build_fixtures.py
KCOMPACT_HIDDEN_ROOT=/opt/verifier-fixtures/kcompactctl python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/kcompactctl ./cmd/kcompactctl
test -x /app/bin/kcompactctl
echo "go-kafka-compacted-topic-snapshot-curator oracle ready"
