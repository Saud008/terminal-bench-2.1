#!/usr/bin/env bash

write_apply_export() {
  local scenario="$1"
  local seed="$2"
  local now_epoch="$3"
  local tree_file="$4"
  local actions_json="$5"
  local out="$6"
  python3 - "$scenario" "$seed" "$now_epoch" "$tree_file" "$actions_json" "$out" <<'PY'
import json, os, sys
scenario, seed, now, tree_file, actions_json, out = sys.argv[1:7]
scenario_name = os.path.basename(scenario.rstrip("/")) if scenario.startswith("/") else scenario
doc = json.load(open(tree_file, encoding="utf-8"))
surviving = sorted(doc["paths"].keys())
export = {
    "scenario": scenario_name,
    "seed": seed,
    "now": int(now),
    "surviving_paths": surviving,
    "actions": json.loads(actions_json),
}
json.dump(export, open(out, "w", encoding="utf-8"), indent=2, sort_keys=True)
PY
}

write_generate_export() {
  local scenario="$1"
  local mode="$2"
  local rules_file="$3"
  local out="$4"
  python3 - "$scenario" "$mode" "$rules_file" "$out" <<'PY'
import json, os, sys
scenario, mode, rules_file, out = sys.argv[1:5]
scenario_name = os.path.basename(scenario.rstrip("/")) if scenario.startswith("/") else scenario
lines = []
for raw in open(rules_file, encoding="utf-8"):
    line = raw.strip()
    if line and not line.startswith("#"):
        lines.append(line)
export = {
    "scenario": scenario_name,
    "mode": mode,
    "rule_lines": lines,
    "line_count": len(lines),
}
json.dump(export, open(out, "w", encoding="utf-8"), indent=2, sort_keys=True)
PY
}
