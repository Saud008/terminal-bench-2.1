#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
findings_json="$1"
python3 -c "
import json,sys
rows=json.load(open(sys.argv[1]))
rows.sort(key=lambda f:(f['category'],f['host'],f['var_key']))
json.dump(rows, sys.stdout)
" "$findings_json"
