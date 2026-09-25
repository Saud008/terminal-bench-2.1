#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pk_map_subject() {
  local subject_json="$1"
  local allow_active="$2"
  local allow_inactive="$3"
  python3 - "$subject_json" "$allow_active" "$allow_inactive" <<'PY'
import json, sys
subject = json.loads(sys.argv[1])
allow_active = sys.argv[2]
allow_inactive = sys.argv[3]
active = bool(subject["active"])
print(allow_active if active else allow_inactive)
PY
}
