#!/usr/bin/env bash

source /app/lib/primary.sh

assign_lineage_ranks() {
  local packages_json="$1"
  python3 - "$packages_json" <<'PY'
import json, sys
packages = json.loads(sys.argv[1])
for pkg in packages:
    pkg["nevra"] = f"{pkg['name']}-{pkg['version']}-{pkg['release']}.{pkg['arch']}"
groups = {}
for pkg in packages:
    key = (pkg["name"], pkg["arch"])
    groups.setdefault(key, []).append(pkg)
out = []
for key in sorted(groups):
    rows = sorted(groups[key], key=lambda p: p["version"], reverse=True)
    for rank, pkg in enumerate(rows, start=1):
        pkg = dict(pkg)
        pkg["lineage_rank"] = rank
        out.append(pkg)
print(json.dumps(out))
PY
}
