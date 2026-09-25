#!/usr/bin/env bash
# Export only after notify barrier; write export-ready marker.

kv_export_state() {
  local staging_path="$1"
  local output_path="$2"
  local last_event_id="$3"
  python3 - "${staging_path}" "${output_path}" "${last_event_id}" <<'PY'
import json, sys, os
from pathlib import Path
staging = json.load(open(sys.argv[1], encoding="utf-8"))
if not staging.get("notify_complete", True):
    sys.exit(0)
out = Path(sys.argv[2])
last_id = sys.argv[3] if sys.argv[3] else None
weights = []
for name in sorted(staging["tracks"], key=lambda s: s.encode()):
    meta = staging["tracks"][name]
    if meta["weight_active"]:
        weights.append({"track": name, "weight": int(meta["weight_value"])})
body = {
    "version": 1,
    "virtual_router_id": staging["virtual_router_id"],
    "role": staging["role"],
    "effective_priority": staging["effective_priority"],
    "advert_seq": staging["advert_seq"],
    "active_weights": weights,
    "last_event_id": last_id,
}
out.parent.mkdir(parents=True, exist_ok=True)
tmp = out.with_suffix(out.suffix + ".tmp")
tmp.write_text(json.dumps(body, separators=(",", ":")) + "\n", encoding="utf-8")
fd = os.open(tmp, os.O_RDONLY)
os.fsync(fd)
os.close(fd)
tmp.replace(out)
fd = os.open(out, os.O_RDONLY)
os.fsync(fd)
os.close(fd)
ready = Path("/app/state/export-ready")
ready.write_text(out.name + "\n", encoding="utf-8")
PY
}

kv_config_check() {
  local conf_path="$1"
  local cfg_path="$2"
  local output_path="$3"
  python3 - "${conf_path}" "${cfg_path}" "${output_path}" <<'PY'
import json, subprocess, sys
from pathlib import Path
conf, cfg_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(cfg_path, encoding="utf-8"))
names = []
for line in open(conf, encoding="utf-8"):
    line = line.strip()
    if line.startswith("chk_"):
        names.append(line)
track_by = {t["name"]: t for t in cfg["tracks"]}
tracks_checked, scripts_run = [], []
all_ok = True
for name in names:
    script = track_by[name]["script"]
    proc = subprocess.run([script], capture_output=True, text=True, check=False)
    tracks_checked.append(name)
    scripts_run.append({"track": name, "exit_code": proc.returncode})
    if proc.returncode != 0:
        all_ok = False
report = {"tracks_checked": tracks_checked, "scripts_run": scripts_run, "all_scripts_ok": all_ok}
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(json.dumps(report, separators=(",", ":")) + "\n", encoding="utf-8")
PY
}
