#!/usr/bin/env bash
# Baseline resume-slot gate blocks on any non-empty resume_token, ignoring resume_cleared.
set -euo pipefail
python3 - <<'PY'
import json, sys
from pathlib import Path
inv = json.loads(Path("/app/state/inventory.json").read_text())
blocked = {}
for adapter in inv.get("adapters", []):
    adapter_id = adapter["adapter_id"]
    for dev in adapter.get("devices", []):
        key = f'{adapter_id}|{dev["mac"]}'
        token = dev.get("resume_token") or ""
        if token:
            blocked[key] = "ineligible_resume_armed"
json.dump(blocked, sys.stdout)
PY
