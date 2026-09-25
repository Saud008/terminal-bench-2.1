#!/usr/bin/env bash
# Hook discovery and topological ordering — oracle implementation.

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
  python3 -c '
import json, sys
hooks = [json.loads(line) for line in sys.stdin if line.strip()]
by_name = {h["name"]: h for h in hooks}
missing = {p for h in hooks for p in h["prereqs"] if p not in by_name}
if missing:
    raise SystemExit(2)
indeg = {h["name"]: 0 for h in hooks}
children = {h["name"]: [] for h in hooks}
for h in hooks:
    for p in h["prereqs"]:
        indeg[h["name"]] += 1
        children[p].append(h["name"])
ready = [h for h in hooks if indeg[h["name"]] == 0]
order = []
while ready:
    ready.sort(key=lambda h: (h["order"], h["name"]))
    cur = ready.pop(0)
    order.append(cur)
    for child in children[cur["name"]]:
        indeg[child] -= 1
        if indeg[child] == 0:
            ready.append(by_name[child])
if len(order) != len(hooks):
    raise SystemExit(2)
for h in order:
    print(json.dumps(h, separators=(",", ":")))
'
}
