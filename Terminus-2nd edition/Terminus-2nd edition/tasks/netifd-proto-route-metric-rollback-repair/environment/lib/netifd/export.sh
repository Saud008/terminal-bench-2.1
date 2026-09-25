#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

netifd_write_export() {
  local output_path="$1"
  python3 - "$NETIFD_SNAPSHOT" "$output_path" <<'PY'
import json
import sys
from pathlib import Path

snap = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
routes = list(snap.get("routes", []))
routes.sort(key=lambda r: r.get("dst", ""))
export_doc = {
    "scenario": snap.get("scenario"),
    "iface": snap.get("iface"),
    "routes": routes,
    "addresses": snap.get("addresses", []),
    "pd_leases": snap.get("pd_leases", []),
    "rules": snap.get("rules", []),
    "rules_committed": snap.get("rules_committed", False),
    "teardown_log": snap.get("teardown_log", []),
    "route_binding": snap.get("route_binding", ""),
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(export_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
