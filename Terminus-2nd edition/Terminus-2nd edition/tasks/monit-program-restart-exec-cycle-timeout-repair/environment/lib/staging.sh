#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

monit_write_snapshot() {
  local config_path="$1"
  local scenario_path="$2"
  python3 - "${config_path}" "${scenario_path}" "${MONIT_SNAPSHOT}" <<'PY'
import hashlib
import json
import sys

cfg_path, sc_path, out_path = sys.argv[1:4]
cfg = json.load(open(cfg_path, encoding="utf-8"))
raw = open(sc_path, "rb").read()
sc = json.loads(raw.decode("utf-8"))
snap = {
    "program": cfg["program"],
    "stop_timeout_sec": int(cfg["stop_timeout_sec"]),
    "start_delay_sec": int(cfg["start_delay_sec"]),
    "restart_limit": int(cfg["restart_limit"]),
    "scenario": sc.get("name", sc_path.split("/")[-1]),
    "event_count": len(sc.get("events", [])),
    "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
}
json.dump(snap, open(out_path, "w", encoding="utf-8"), indent=2, sort_keys=True)
PY
}
