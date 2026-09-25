        #!/usr/bin/env bash
        set -euo pipefail

        parse_rule_list() {
          local rules_json="$1"
          python3 - <<'PY' "$rules_json"
import json, sys
rows = json.loads(sys.argv[1])
parsed = []
for i, raw in enumerate(rows):
    raw = str(raw).strip()
    if not raw or raw.startswith("#"):
        continue
    token = raw[0]
    pattern = raw[1:].strip()
    if token == "P":
        token = "-"
    if token == "R":
        token = "-"
    parsed.append({"token": token, "pattern": pattern, "index": i})
print(json.dumps(parsed))
PY
        }
