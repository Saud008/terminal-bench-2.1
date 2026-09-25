#!/usr/bin/env bash
# Baseline GATT catalog counts raw UUID entries without lowercasing or dedupe.
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
counts = {}
for adapter in inv.get("adapters", []):
    adapter_id = adapter["adapter_id"]
    for dev in adapter.get("devices", []):
        key = f'{adapter_id}|{dev["mac"]}'
        uuids = dev.get("gatt_uuids") or []
        counts[key] = len(uuids)
json.dump(counts, sys.stdout)
PY
