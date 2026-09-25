#!/usr/bin/env bash

source /app/lib/primary.sh

assign_lineage_ranks() {
  local packages_json="$1"
  python3 - "$packages_json" <<'PY'
import json, sys

def seg_key(token: str):
    parts = []
    for chunk in token.replace("-", "~").split("."):
        num = ""
        suffix = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                suffix += ch
        parts.append((int(num or 0), suffix))
    return parts

def evra_key(pkg):
    return (pkg["epoch"], seg_key(pkg["version"]), seg_key(pkg["release"]))

packages = json.loads(sys.argv[1])
for pkg in packages:
    pkg["nevra"] = f"{pkg['epoch']}:{pkg['name']}-{pkg['version']}-{pkg['release']}.{pkg['arch']}"
groups = {}
for pkg in packages:
    key = (pkg["name"], pkg["arch"])
    groups.setdefault(key, []).append(pkg)
out = []
for key in sorted(groups):
    rows = sorted(groups[key], key=evra_key, reverse=True)
    for rank, pkg in enumerate(rows, start=1):
        row = dict(pkg)
        row["lineage_rank"] = rank
        out.append(row)
print(json.dumps(out))
PY
}
