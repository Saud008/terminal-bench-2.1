#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
weights="${APP_ROOT}/config/severity-weights.json"
category="$1"
python3 -c "
import json,sys
w=json.load(open(sys.argv[1]))
print(w.get(sys.argv[2],'low'))
" "$weights" "$category"
