#!/usr/bin/env bash
# Evaluate retention policy into staging evaluation block.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/retention.sh"

list_file=""
policy=""
holds=""
reference_now=""
while [ $# -gt 0 ]; do
  case "$1" in
    --list) list_file="$2"; shift 2 ;;
    --policy) policy="$2"; shift 2 ;;
    --holds) holds="$2"; shift 2 ;;
    --now) reference_now="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${list_file}" ] && [ -n "${policy}" ] && [ -n "${holds}" ] && [ -n "${reference_now}" ] \
  || die "evaluate requires --list --policy --holds --now"

stage="$(stage_path_for "${list_file}")"
require_file "${stage}"
require_file "${policy}"
require_file "${holds}"

eval_json="$(evaluate_retention_json "${stage}" "${policy}" "${holds}" "${reference_now}")"

python3 - "${stage}" "${eval_json}" "${reference_now}" <<'PY'
import json, sys
from pathlib import Path
stage_path, eval_json, ref = sys.argv[1], sys.argv[2], sys.argv[3]
stage = json.loads(Path(stage_path).read_text(encoding="utf-8"))
stage["evaluation"] = json.loads(eval_json)
stage["reference_now"] = ref
with open(stage_path, "w", encoding="utf-8") as fh:
    json.dump(stage, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "evaluated ${stage}"
