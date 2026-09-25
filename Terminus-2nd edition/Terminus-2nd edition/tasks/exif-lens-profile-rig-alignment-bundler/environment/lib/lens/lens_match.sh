#!/usr/bin/env bash
match_lens_profile() {
  local lenses_json="$1"
  local lens_id="$2"
  local normalized_ms="$3"
  python3 - "$lenses_json" "$lens_id" "$normalized_ms" <<'PY'
import json, sys
lenses, lens_id, when = sys.argv[1], sys.argv[2], int(sys.argv[3])
data = json.loads(open(lenses, encoding="utf-8").read())
for row in data.get("profiles", []):
    if row.get("lens_id") == lens_id:
        print(json.dumps(row, separators=(",", ":")))
        raise SystemExit(0)
print("")
PY
}
