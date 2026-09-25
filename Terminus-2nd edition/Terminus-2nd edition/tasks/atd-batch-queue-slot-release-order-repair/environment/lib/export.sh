#!/usr/bin/env bash

emit_export() {
  local scenario_label="$1"
  local seed="$2"
  local clock_epoch="$3"
  local timezone="$4"
  local out="$5"
  local atq_json
  atq_json="$(build_atq_lines)"
  python3 - "$STATE" "$scenario_label" "$seed" "$clock_epoch" "$timezone" "$REGISTRY_DIR" "$SEQ_FILE" "$atq_json" "$out" <<'PY'
import json, sys
from pathlib import Path
state_path, scenario, seed, clock_epoch, timezone, registry_dir, seq_file, atq_json, out = sys.argv[1:10]
state = json.load(open(state_path, encoding="utf-8"))
registry_final = {}
for path in sorted(Path(registry_dir).glob("*.record.json")):
    name = path.name.replace(".record.json", "", 1)
    batch, job_id = name.split(".", 1)
    key = f"{batch}:{job_id}"
    registry_final[key] = json.loads(path.read_text(encoding="utf-8"))
seq_final = 1
if Path(seq_file).is_file():
    seq_final = int(Path(seq_file).read_text(encoding="utf-8").strip())
doc = {
    "export_version": 1,
    "scenario": scenario,
    "seed": seed,
    "clock_epoch": int(clock_epoch),
    "timezone": timezone,
    "jobs_run": state.get("jobs_run", []),
    "jobs_skipped": state.get("jobs_skipped", []),
    "timeline": state.get("timeline", []),
    "registry_final": registry_final,
    "mail_log": state.get("mail_log", []),
    "atq_lines": json.loads(atq_json),
    "seq_final": seq_final,
    "batch_slots_held": state.get("batch_slots_held", []),
}
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
