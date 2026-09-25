#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
host="$1"
inventory_root="$2"
python3 -c "
import json,sys
sys.path.insert(0,'${APP_ROOT}/lib')
from pathlib import Path
from inventory_engine import (
    parse_inventory_ini, effective_vars_for_host, load_ignore_patterns,
    CHILDREN_FIRST, HOST_BEFORE_GROUPS,
)
manifest=json.load(open(sys.argv[3]))
root=Path(manifest['inventory_root'])
cfg=Path(manifest.get('ansible_cfg', root/'ansible.cfg'))
ini=root/'inventory'/'hosts.ini'
if not ini.is_file():
    ini=root/'hosts.ini'
h,c,_=parse_inventory_ini(ini.read_text())
patterns=load_ignore_patterns(root,cfg)
eff,_=effective_vars_for_host(root,sys.argv[1],h,c,patterns,CHILDREN_FIRST,HOST_BEFORE_GROUPS)
json.dump(eff, sys.stdout)
" "$host" "$inventory_root" "${3:-/dev/null}"
