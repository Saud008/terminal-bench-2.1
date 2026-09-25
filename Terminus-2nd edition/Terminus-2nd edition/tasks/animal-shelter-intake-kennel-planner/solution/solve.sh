# Oracle solve — task identity animal-shelter-intake-kennel-planner token 33bc373d
#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app
bash "${ROOT_DIR}/apply_frontier.sh"
python3 /app/fixtures/build_registry_scenarios.py
if [ -d /opt/verifier-fixtures/intakectl ]; then
  KENNEL_HIDDEN_ROOT=/opt/verifier-fixtures/intakectl python3 /app/fixtures/build_registry_scenarios.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/intakectl ./cmd/intakectl
test -x /app/bin/intakectl
echo "animal-shelter-intake-kennel-planner oracle ready"
