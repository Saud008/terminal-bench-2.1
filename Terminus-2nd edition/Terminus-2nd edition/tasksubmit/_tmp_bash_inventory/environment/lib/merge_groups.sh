#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
# merge_groups.sh records lineage expansion for audit trace
host="$1"
inventory_root="$2"
shift 2
python3 -c "
import json,sys
sys.path.insert(0,'${APP_ROOT}/lib')
from pathlib import Path
from inventory_engine import parse_inventory_ini, host_groups, CHILDREN_FIRST
root=Path(sys.argv[1])
ini=root/'inventory'/'hosts.ini'
if not ini.is_file():
    ini=root/'hosts.ini'
text=ini.read_text()
h,c,_=parse_inventory_ini(text)
groups=host_groups(sys.argv[2], h, c, children_first=CHILDREN_FIRST)
json.dump({'host':sys.argv[2],'groups':groups}, sys.stdout)
" "$inventory_root" "$host"
