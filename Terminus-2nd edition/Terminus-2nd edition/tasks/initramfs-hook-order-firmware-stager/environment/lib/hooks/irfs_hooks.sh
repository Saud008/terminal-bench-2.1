#!/usr/bin/env bash
# Hook discovery and ordering — baseline name sort only.

irfs_discover_hooks() {
  local root="$1"
  ROOTFS="${root}" python3 <<'PY'
import json, os, re
from pathlib import Path
root = Path(os.environ["ROOTFS"])
hooks_dir = root / "hooks"
if not hooks_dir.is_dir():
    raise SystemExit(0)
for path in sorted(hooks_dir.glob("*.sh")):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^(\d+)-(.+)\.sh$", path.name)
    if not m:
        continue
    order = int(m.group(1))
    name = m.group(2)
    prereqs = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# PREREQ="):
            raw = line.split("=", 1)[1].strip()
            prereqs = [p.strip() for p in raw.split(",") if p.strip()]
        elif line.startswith("# HOOK="):
            name = line.split("=", 1)[1].strip()
    rel = path.relative_to(root).as_posix()
    print(json.dumps({"name": name, "order": order, "path": rel, "prereqs": prereqs}, separators=(",", ":")))
PY
}

irfs_topo_sort_hooks() {
  # baseline: sorts by name only, ignores prereq DAG
  python3 -c '
import json, sys
hooks = [json.loads(line) for line in sys.stdin if line.strip()]
hooks.sort(key=lambda h: h["name"])
for h in hooks:
    print(json.dumps(h, separators=(",", ":")))
'
}
