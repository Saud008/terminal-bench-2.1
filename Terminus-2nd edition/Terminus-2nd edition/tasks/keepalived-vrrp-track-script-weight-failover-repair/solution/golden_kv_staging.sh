#!/usr/bin/env bash
# Staging — refresh effective priority after track recovery.

kv_apply_track_event() {
  local staging_path="$1"
  local cfg_path="$2"
  local track="$3"
  local status="$4"
  python3 - "${staging_path}" "${cfg_path}" "${track}" "${status}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
cfg = json.load(open(sys.argv[2], encoding="utf-8"))
name, status = sys.argv[3], sys.argv[4]
meta = staging["tracks"][name]
tcfg = next(t for t in cfg["tracks"] if t["name"] == name)
if status == "fail":
    meta["consecutive_fail"] += 1
    meta["consecutive_ok"] = 0
else:
    meta["consecutive_ok"] += 1
    meta["consecutive_fail"] = 0
    if meta["weight_active"] and meta["consecutive_ok"] >= int(tcfg["rise"]):
        meta["weight_active"] = False
        base = int(staging["base_priority"])
        floor = int(staging["priority_floor"])
        active = sum(int(m["weight_value"]) for m in staging["tracks"].values() if m["weight_active"])
        staging["effective_priority"] = max(floor, base + active)
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}

kv_write_staging_snapshot() {
  local staging_path="$1"
  local snapshot_path="$2"
  local manifest_path="$3"
  local input_path="$4"
  python3 - "${staging_path}" "${snapshot_path}" "${manifest_path}" "${input_path}" <<'PY'
import hashlib, json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
staging.pop("_prev_role", None)
snap_path, man_path, inp = sys.argv[2], sys.argv[3], sys.argv[4]
with open(snap_path, "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"), sort_keys=True)
    fh.write("\n")
inp_d = hashlib.sha256(open(inp, "rb").read()).hexdigest()
snap_d = hashlib.sha256(open(snap_path, "rb").read()).hexdigest()
manifest = {"input_sha256": inp_d, "snapshot_sha256": snap_d}
with open(man_path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, separators=(",", ":"))
    fh.write("\n")
PY
}

kv_init_staging() {
  local cfg_path="$1"
  local staging_path="$2"
  python3 - "${cfg_path}" "${staging_path}" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
tracks = {}
for t in cfg["tracks"]:
    tracks[t["name"]] = {
        "consecutive_fail": 0,
        "consecutive_ok": 0,
        "weight_active": False,
        "weight_value": int(t["weight"]),
    }
base = int(cfg["base_priority"])
staging = {
    "virtual_router_id": int(cfg["virtual_router_id"]),
    "base_priority": base,
    "priority_floor": int(cfg["priority_floor"]),
    "master_threshold": int(cfg["master_threshold"]),
    "effective_priority": base,
    "role": "MASTER" if base >= int(cfg["master_threshold"]) else "BACKUP",
    "advert_seq": 0,
    "notify_pending": False,
    "notify_complete": True,
    "applied_event_ids": [],
    "tracks": tracks,
}
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
