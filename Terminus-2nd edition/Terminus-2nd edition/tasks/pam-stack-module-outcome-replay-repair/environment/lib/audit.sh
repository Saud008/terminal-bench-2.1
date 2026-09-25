#!/usr/bin/env bash
# Audit JSONL writer.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

: "${PAMREPLAY_AUDIT_PATH:=}"
: "${PAMREPLAY_AUDIT_BUFFER:=[]}"

pamreplay_audit_reset() {
  PAMREPLAY_AUDIT_BUFFER="[]"
}

pamreplay_audit_set_path() {
  PAMREPLAY_AUDIT_PATH="$1"
}

pamreplay_audit_record() {
  local phase="$1"
  local module="$2"
  local control="$3"
  local rc="$4"
  PAMREPLAY_AUDIT_BUFFER="$(python3 - "$phase" "$module" "$control" "$rc" "$PAMREPLAY_AUDIT_BUFFER" <<'PY'
import json, sys
phase, module, control, rc, buf = sys.argv[1:6]
rows = json.loads(buf)
phase_seq = sum(1 for row in rows if row["phase"] == phase) + 1
rows.append({"seq": phase_seq, "phase": phase, "module": module, "control": control, "rc": int(rc)})
print(json.dumps(rows))
PY
)"
}

pamreplay_audit_flush() {
  local path="$1"
  python3 - "$path" "$PAMREPLAY_AUDIT_BUFFER" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
rows = json.loads(sys.argv[2])
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("w", encoding="utf-8") as fh:
    for row in rows:
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")
PY
}

pamreplay_audit_flush_before_rollback() {
  pamreplay_audit_flush "$1"
}
