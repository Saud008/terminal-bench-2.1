#!/usr/bin/env bash

locate_message() {
  local qid="$1"
  local qclass="$2"
  local subdir=""
  subdir="$(python3 - "$qid" <<'PY'
import json, sys
from pathlib import Path
qid = sys.argv[1]
manifest = Path("/app/state/spool-manifest.json")
if not manifest.is_file():
    raise SystemExit(1)
doc = json.load(manifest.open(encoding="utf-8"))
for row in doc.get("messages", []):
    if row.get("quarantine_id") == qid:
        print(row.get("spool_subdir", row.get("stored_class", "spam")))
        raise SystemExit(0)
raise SystemExit(1)
PY
)" || subdir=""
  if [[ -n "$subdir" ]]; then
    SPOOL_DIR="/app/work/spool/${subdir}"
    msg_paths "$SPOOL_DIR" "$qid"
    [[ -f "$MSG_EML" ]] && return 0
  fi
  spool_for_class "$qclass"
  msg_paths "$SPOOL_DIR" "$qid"
}
