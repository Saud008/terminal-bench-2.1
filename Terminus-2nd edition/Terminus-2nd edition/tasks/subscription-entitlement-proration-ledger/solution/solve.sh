# Oracle solve — task identity subscription-entitlement-proration-ledger token ee61d280
# Oracle solve — subscription-entitlement-proration-ledger
#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app
bash "${ROOT_DIR}/apply_frontier.sh"
python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/subledctl ./cmd/subledctl
test -x /app/bin/subledctl
python3 <<'PY'
from pathlib import Path
import json

cycles = sorted(Path("/app/fixtures/cycles").glob("*.json"))
assert len(cycles) >= 9, [p.name for p in cycles]
for path in cycles:
    body = json.loads(path.read_text(encoding="utf-8"))
    assert body.get("scenario_id") == path.stem
    assert isinstance(body.get("plans"), dict) and body["plans"]
    assert isinstance(body.get("events"), list)
    assert "customer_id" in body
    assert "cycle_start" in body and "cycle_end" in body
report = {
    "scenario_count": len(cycles),
    "scenario_ids": [p.stem for p in cycles],
}
Path("/app/state/oracle-fixture-check.json").write_text(
    json.dumps(report, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
PY
echo "subscription-entitlement-proration-ledger oracle ready"
