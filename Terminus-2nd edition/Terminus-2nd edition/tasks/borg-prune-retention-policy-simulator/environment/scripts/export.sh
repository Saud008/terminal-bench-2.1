#!/usr/bin/env bash
# Export dry-run prune report from staging evaluation.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

list_file=""
out=""
while [ $# -gt 0 ]; do
  case "$1" in
    --list) list_file="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${list_file}" ] && [ -n "${out}" ] || die "export requires --list and --out"

stage="$(stage_path_for "${list_file}")"
require_file "${stage}"

python3 - "${stage}" "${out}" <<'PY'
import json, sys
from pathlib import Path

stage = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = sys.argv[2]
if "evaluation" not in stage:
    raise SystemExit("missing evaluation block")
ev = stage["evaluation"]
archives = {a["name"]: a for a in stage["archives"]}
kept = ev["kept"]
pruned = ev["pruned"]
compaction_bytes = sum(archives[n]["bytes"] for n in kept if n in archives)
compaction_segments = sum(archives[n]["segments"] for n in kept if n in archives)
doc = {
    "clock_skew_adjustment_count": len(ev.get("clock_skew_adjusted", [])),
    "compaction_bytes_reclaimable": compaction_bytes,
    "compaction_segments_reclaimable": compaction_segments,
    "kept_archives": kept,
    "legal_hold_count": len(ev.get("legal_hold_kept", [])),
    "pruned_archives": pruned,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "exported ${out}"
