#!/usr/bin/env bash
# Export plan JSON (legacy path; staging digest gate omitted).

export_plan_emit() {
  local output_path="$1"
  local manifest_dir="$2"
  local _manifest_file="$3"
  local _config_path="$4"
  local mod_count="$5"
  local edge_count="$6"
  local _exit_code="$7"

  mkdir -p "$(dirname "${output_path}")"

  export PLAN_MANIFEST_DIR="${manifest_dir}"
  export PLAN_MOD_COUNT="${mod_count}"
  export PLAN_EDGE_COUNT="${edge_count}"
  export PLAN_RUN_SEQ="1"
  export PLAN_MOUNT_JSON="$(printf '%s\n' "${TOPO_ORDER[@]-}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"
  export PLAN_ERRORS_JSON="$(printf '%s\n' "${DEPS_ERRORS[@]-}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"
  export PLAN_CYCLES_JSON="$(printf '%s\n' "${TOPO_CYCLES[@]-}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"

  python3 - "${output_path}" <<'PY'
import json
import os
import sys

doc = {
    "plan_version": 1,
    "manifest_dir": os.environ["PLAN_MANIFEST_DIR"],
    "mount_order": json.loads(os.environ["PLAN_MOUNT_JSON"]),
    "errors": json.loads(os.environ["PLAN_ERRORS_JSON"]),
    "cycles": json.loads(os.environ["PLAN_CYCLES_JSON"]),
    "stats": {
        "mod_count": int(os.environ["PLAN_MOD_COUNT"]),
        "edge_count": int(os.environ["PLAN_EDGE_COUNT"]),
    },
    "footer": {"run_seq": int(os.environ["PLAN_RUN_SEQ"])},
}
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}
