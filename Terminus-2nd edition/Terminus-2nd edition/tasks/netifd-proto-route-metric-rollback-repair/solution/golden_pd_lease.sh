#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

netifd_pd_acquire() {
  local scenario_json="$1" iface="$2"
  local prefix lease_id
  prefix="$(python3 - "$scenario_json" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
print(data.get("pd_prefix") or "")
PY
)"
  lease_id="$(python3 - "$scenario_json" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
print(data.get("pd_lease_id") or "pd-default")
PY
)"
  [[ -z "$prefix" ]] && return 0
  harness_py pd_acquire "$iface" "$prefix" "$lease_id"
}

netifd_pd_release_for_reload() {
  local iface="$1"
  harness_py pd_release_iface "$iface"
}
