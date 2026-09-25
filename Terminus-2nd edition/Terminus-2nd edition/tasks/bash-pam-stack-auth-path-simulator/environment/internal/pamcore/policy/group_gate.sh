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
direct = set(users.get(subject, {}).get("groups", []))
# direct group list only
print(json.dumps(sorted(direct)))
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
