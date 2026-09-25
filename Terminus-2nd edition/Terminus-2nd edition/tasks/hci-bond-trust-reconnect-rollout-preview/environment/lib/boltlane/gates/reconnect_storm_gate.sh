#!/usr/bin/env bash
# Baseline reconnect-storm gate counts every battery probe, ignoring debounce_ms.
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
cfg = json.loads(Path("/app/config/hciroll.json").read_text())
max_reconnects = int(cfg["max_reconnects_per_window"])
blocked = {}
attempts_map = {}
for adapter in inv.get("adapters", []):
    adapter_id = adapter["adapter_id"]
    for dev in adapter.get("devices", []):
        key = f'{adapter_id}|{dev["mac"]}'
        probes = dev.get("battery_probes_ms") or []
        attempts = len(probes)
        attempts_map[key] = attempts
        if attempts > max_reconnects:
            blocked[key] = "ineligible_reconnect_storm"
json.dump({"blocked": blocked, "attempts": attempts_map}, sys.stdout)
PY
