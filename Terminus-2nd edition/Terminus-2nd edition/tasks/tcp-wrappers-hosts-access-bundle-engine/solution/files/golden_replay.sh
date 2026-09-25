#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

replay_session() {
  local root="$1"
  local session_path="$2"
  local export_path="$3"
  local manifest name payload rc
  manifest="$(read_manifest "$root")"
  name="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["name"])
PY
)"
  payload="$(python3 - "$name" "$session_path" "$root" <<'PY'
import json
import os
import subprocess
import sys
import tempfile

name, session_path, root = sys.argv[1:4]
entries = json.load(open(session_path, encoding="utf-8"))
mismatches = []
for entry in entries:
    daemon = entry["daemon"]
    ip = entry["ip"]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".json") as fh:
        out = fh.name
    proc = subprocess.run(
        [
            "hostsctl",
            "decide",
            "--bundle",
            root,
            "--daemon",
            daemon,
            "--ip",
            ip,
            "--export",
            out,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        mismatches.append({"daemon": daemon, "ip": ip, "error": (proc.stderr or proc.stdout).strip()})
        os.unlink(out)
        continue
    got = json.loads(open(out, encoding="utf-8").read())
    os.unlink(out)
    if got["decision"] != entry["decision"] or got["matched_rule_index"] != entry["matched_rule_index"]:
        mismatches.append({"daemon": daemon, "ip": ip, "expected": entry, "actual": got})
print(json.dumps({"bundle": name, "checked": len(entries), "mismatches": mismatches}, indent=2))
raise SystemExit(1 if mismatches else 0)
PY
)"
  rc=$?
  json_write "$export_path" "$payload"
  return "$rc"
}
