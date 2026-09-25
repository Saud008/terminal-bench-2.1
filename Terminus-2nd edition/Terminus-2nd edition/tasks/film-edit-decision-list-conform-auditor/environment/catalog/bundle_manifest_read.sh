#!/usr/bin/env bash
# Read bundle manifest paths for catalog tooling (not on stage hot path).
set -euo pipefail

manifest="$1"
python3 - "${manifest}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for key in ("bundle_id", "edl", "sources", "aliases", "missing", "tc_map"):
    print(d.get(key, ""))
PY
