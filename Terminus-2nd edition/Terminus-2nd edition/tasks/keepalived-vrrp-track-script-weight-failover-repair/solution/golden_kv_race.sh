#!/usr/bin/env bash
# Simultaneous fall — activate every candidate in config order.

kv_apply_fall_race() {
  local staging_path="$1"
  local cfg_path="$2"
  local ts="$3"
  python3 - "${staging_path}" "${cfg_path}" "${ts}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
cfg = json.load(open(sys.argv[2], encoding="utf-8"))
order = {t["name"]: i for i, t in enumerate(cfg["tracks"])}
candidates = []
for name, meta in staging["tracks"].items():
    tcfg = next(t for t in cfg["tracks"] if t["name"] == name)
    if meta["consecutive_fail"] >= int(tcfg["fall"]) and not meta["weight_active"]:
        candidates.append(name)
activated = 0
for name in sorted(candidates, key=lambda n: order.get(n, 999)):
    staging["tracks"][name]["weight_active"] = True
    activated = 1
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
print(activated)
PY
}
