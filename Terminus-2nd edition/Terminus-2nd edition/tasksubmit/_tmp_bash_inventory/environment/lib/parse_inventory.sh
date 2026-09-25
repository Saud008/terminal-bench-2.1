#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
ini="$1"
python3 -c "
import json,sys
sys.path.insert(0,'${APP_ROOT}/lib')
from inventory_engine import parse_inventory_ini
text=open(sys.argv[1]).read()
h,c,m=parse_inventory_ini(text)
json.dump({'merge_order':m,'hosts_by_group':h,'children_by_group':c}, sys.stdout)
" "$ini"
