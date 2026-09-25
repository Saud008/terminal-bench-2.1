#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_find_orphans() {
  local merged_json="$1"
  python3 - "${merged_json}" <<'PY'
import json, re, sys

merged = json.loads(sys.argv[1])
uid_re = re.compile(r'uid="(uid://[^"]+)"')
present = set()
refs = []

for rel, text in merged.items():
    for line in text.splitlines():
        if line.startswith("[gd_scene") and 'uid="' in line:
            m = uid_re.search(line)
            if m:
                present.add(m.group(1))
            break
    for i, line in enumerate(text.splitlines(), start=1):
        for m in uid_re.finditer(line):
            uid = m.group(1)
            if line.startswith("[gd_scene") and i == 1:
                continue
            refs.append((rel, uid))

orphans = []
seen = set()
for rel, uid in refs:
    key = (rel, uid)
    if key in seen:
        continue
    seen.add(key)
    if uid not in present:
        orphans.append({"file": rel, "uid": uid})
print(json.dumps(orphans))
PY
}
