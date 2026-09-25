#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../include/expand_includes.sh"

build_ledger() {
  local run_id="$1"
  local load_json="$2"
  python3 - "$run_id" "$load_json" <<'PY'
import json, sys, hashlib
from pathlib import Path

run_id = sys.argv[1]
load = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
scenario = Path(load["scenario_root"])
services = {}
for svc_file in sorted((scenario / "services").glob("*")):
    if not svc_file.is_file():
        continue
    import subprocess
    expanded = json.loads(subprocess.check_output(
        ["bash", "-c", f'source /app/internal/pamcore/include/expand_includes.sh; expand_service_file "{svc_file}"'],
        text=True,
    ))
    auth_modules = [m for m in expanded if m.get("kind") == "module" and m.get("type") == "auth"]
    fp = hashlib.sha256(json.dumps(auth_modules, sort_keys=True).encode()).hexdigest()
    services[svc_file.name] = {
        "service": svc_file.name,
        "modules": auth_modules,
        "service_fingerprint": fp,
    }
outcomes = json.loads((scenario / "modules.json").read_text(encoding="utf-8"))
subjects = json.loads((scenario / "subjects.json").read_text(encoding="utf-8"))
body = {
    "run_id": run_id,
    "scenario": load["scenario"],
    "services": services,
    "outcomes": outcomes,
    "subjects": subjects,
}
fp_src = json.dumps({"run_id": run_id, "services": {k: v["service_fingerprint"] for k, v in services.items()}}, sort_keys=True)
body["ledger_fingerprint"] = hashlib.sha256(fp_src.encode()).hexdigest()
print(json.dumps(body))
PY
}
