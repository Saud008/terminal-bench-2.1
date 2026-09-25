#!/usr/bin/env bash
set -euo pipefail

subject_groups() {
  local subjects_json="$1"
  local subject="$2"
  python3 - "$subjects_json" "$subject" <<'PY'
import json, sys
doc = json.loads(sys.argv[1])
subject = sys.argv[2]
users = doc.get("users", {})
groups = doc.get("groups", {})

def member_closure(name, seen=None):
    seen = seen or set()
    if name in seen:
        return set()
    seen.add(name)
    out = {name}
    for child in groups.get(name, []):
        if child in groups:
            out |= member_closure(child, seen)
        else:
            out.add(child)
    return out

direct = users.get(subject, {}).get("groups", [])
effective = set(direct) | {subject}
for g in direct:
    effective |= member_closure(g)
changed = True
while changed:
    changed = False
    for gname, members in groups.items():
        if gname in effective:
            continue
        if any(m in effective for m in members):
            effective.add(gname)
            changed = True
print(json.dumps(sorted(effective)))
PY
}

group_allows() {
  local subjects_json="$1"
  local subject="$2"
  local required_group="$3"
  local member_groups
  member_groups="$(subject_groups "$subjects_json" "$subject")"
  echo "$member_groups" | jq -e --arg g "$required_group" 'index($g) != null' >/dev/null
}
