#!/usr/bin/env bash
# Simultaneous fall activation when multiple tracks cross fall threshold.

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
if not candidates:
    pass
elif len(candidates) > 1:
    pick = sorted(candidates)[-1]
    staging["tracks"][pick]["weight_active"] = True
    activated = 1
else:
    staging["tracks"][candidates[0]]["weight_active"] = True
    activated = 1
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
print(activated)
PY
}
