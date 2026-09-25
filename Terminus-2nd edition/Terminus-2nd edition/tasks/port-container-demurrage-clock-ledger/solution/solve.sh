# Oracle solve — task identity port-container-demurrage-clock-ledger token c4e8f2a1
#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app
bash "${ROOT_DIR}/apply_frontier.sh"
python3 - <<'PY'
from pathlib import Path

required = [
    Path("/app/internal/holdpolicy/precedence.go"),
    Path("/app/internal/closurecal/exclude.go"),
    Path("/app/internal/pauseclock/clock_runner.go"),
    Path("/app/internal/tarifftier/tier_calc.go"),
    Path("/app/internal/invoicewriter/publish.go"),
    Path("/app/internal/yardbundle/event_sort.go"),
]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise SystemExit("oracle frontier incomplete: " + ", ".join(missing))
PY
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/demurctl ]; then
  DEMUR_HIDDEN_ROOT=/opt/verifier-fixtures/demurctl python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/demurctl ./cmd/demurctl
test -x /app/bin/demurctl
echo "port-container-demurrage-clock-ledger oracle ready"
