#!/usr/bin/env bash
set -euo pipefail

parse_wg_conf() {
  local path="$1"
  python3 - <<'PY' "$path"
import json, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
iface, peers, cur, section = {}, [], {}, None
for line in text.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("[") and line.endswith("]"):
        if section == "Peer" and cur:
            peers.append(cur)
            cur = {}
        section = line[1:-1]
        continue
    if "=" not in line:
        continue
    k, v = line.split("=", 1)
    k, v = k.strip(), v.strip()
    if section == "Interface":
        iface[k] = v
    elif section == "Peer":
        if k == "AllowedIPs":
            cur[k] = [p.strip() for p in v.split(",") if p.strip()]
        elif k == "Name":
            cur[k] = v
        else:
            cur[k] = v
if section == "Peer" and cur:
    peers.append(cur)
print(json.dumps({"interface": iface, "peers": peers}))
PY
}
