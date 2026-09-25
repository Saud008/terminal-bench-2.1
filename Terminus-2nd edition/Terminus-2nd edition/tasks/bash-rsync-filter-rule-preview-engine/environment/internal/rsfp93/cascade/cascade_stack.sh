        #!/usr/bin/env bash
        set -euo pipefail

        cascaded_rules_for_path() {
          local path="$1"
          local root_rules_json="$2"
          local cascade_overlays_json="$3"
          python3 - <<'PY' "$path" "$root_rules_json" "$cascade_overlays_json"
import json, os, sys
path = sys.argv[1]
root = json.loads(sys.argv[2])
cascade_overlays = json.loads(sys.argv[3])
dirs = []
acc = []
for segment in path.split("/")[:-1]:
    acc.append(segment)
    dirs.append("/".join(acc))

out = []
ledger = []
for d in reversed(dirs):
    rows = cascade_overlays.get(d, [])
    if rows:
        out.extend(rows)
        ledger.append({"directory": d, "added_rules": len(rows)})
out.extend(root)
ledger.append({"directory": "/", "added_rules": len(root)})
print(json.dumps({"rules": out, "cascade_depth": len(dirs), "rule_cascade": ledger}))
PY
        }
