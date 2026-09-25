# Oracle solve — task identity event-ticket-seat-hold-reconciliation token b343b3d0
#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app
bash "${ROOT_DIR}/apply_frontier.sh"
python3 - <<'PY'
from pathlib import Path

required = [
    Path("/app/internal/expirygate/boundary.go"),
    Path("/app/internal/captureorder/sort.go"),
    Path("/app/internal/rowguard/block.go"),
    Path("/app/internal/accessfloor/inventory.go"),
    Path("/app/internal/holddigest/fingerprint.go"),
    Path("/app/internal/passseal/stamp.go"),
    Path("/app/internal/seatledger/status.go"),
    Path("/app/internal/mapapply/map.go"),
]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise SystemExit("oracle frontier incomplete: " + ", ".join(missing))
PY
python3 /app/fixtures/build_scenarios.py
if [ -d /opt/verifier-fixtures/venuetixctl ]; then
  VENUETIX_HIDDEN_ROOT=/opt/verifier-fixtures/venuetixctl python3 /app/fixtures/build_scenarios.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/venuetixctl ./cmd/venuetixctl
test -x /app/bin/venuetixctl
echo "event-ticket-seat-hold-reconciliation oracle ready"
