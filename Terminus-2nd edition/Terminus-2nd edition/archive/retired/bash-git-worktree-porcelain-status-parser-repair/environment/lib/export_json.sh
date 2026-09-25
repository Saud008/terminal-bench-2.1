#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

wt_write_export() {
  local porcelain_path="$1"
  local config_path="$2"
  local export_path="$3"
  local entries_json="$4"
  python3 - "${porcelain_path}" "${config_path}" "${export_path}" "${entries_json}" <<'PY'
import json
import sys
from pathlib import Path

porcelain, config_path, export_path, entries_json = sys.argv[1:5]
cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
entries = json.loads(entries_json)
summary = {
    "ordinary": 0,
    "rename": 0,
    "copy": 0,
    "unmerged": 0,
    "untracked": 0,
    "ignored": 0,
}
for entry in entries:
    summary[entry["kind"]] += 1
doc = {
    "porcelain": porcelain,
    "config": config_path,
    "rename_score_min": int(cfg["rename_score_min"]),
    "entries": entries,
    "summary": summary,
}
Path(export_path).parent.mkdir(parents=True, exist_ok=True)
Path(export_path).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}
