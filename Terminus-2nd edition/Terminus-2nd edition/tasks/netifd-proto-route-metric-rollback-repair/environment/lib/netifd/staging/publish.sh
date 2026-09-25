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
routes = payload.get("routes", [])
dsts = sorted(r.get("dst", "") for r in routes)
digest = hashlib.sha256(json.dumps(dsts, separators=(",", ":")).encode()).hexdigest()
payload["route_binding"] = digest
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
