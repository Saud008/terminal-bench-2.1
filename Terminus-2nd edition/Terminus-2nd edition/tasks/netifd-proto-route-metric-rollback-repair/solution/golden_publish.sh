#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"

netifd_publish_snapshot() {
  local payload="$1"
  python3 - "$payload" "$NETIFD_SNAPSHOT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

payload = json.loads(sys.argv[1])
out = Path(sys.argv[2])
parts = [
    payload["scenario"],
    payload["iface"],
    json.dumps(payload.get("routes", []), separators=(",", ":"), ensure_ascii=False),
    json.dumps(payload.get("addresses", []), separators=(",", ":"), ensure_ascii=False),
    json.dumps(payload.get("pd_leases", []), separators=(",", ":"), ensure_ascii=False),
    json.dumps(payload.get("rules", []), separators=(",", ":"), ensure_ascii=False),
    json.dumps(payload.get("teardown_log", []), separators=(",", ":"), ensure_ascii=False),
]
payload["route_binding"] = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
payload["schema"] = 1
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

netifd_read_snapshot() {
  python3 - "$NETIFD_SNAPSHOT" <<'PY'
import json, sys
from pathlib import Path
print(Path(sys.argv[1]).read_text(encoding="utf-8"))
PY
}
