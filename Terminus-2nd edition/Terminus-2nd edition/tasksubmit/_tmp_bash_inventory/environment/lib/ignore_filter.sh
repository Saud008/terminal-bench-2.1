#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
inventory_root="$1"
ansible_cfg="$2"
python3 -c "
import json,sys
sys.path.insert(0,'${APP_ROOT}/lib')
from pathlib import Path
from inventory_engine import load_ignore_patterns
p=load_ignore_patterns(Path(sys.argv[1]), Path(sys.argv[2]) if sys.argv[2] else None)
json.dump(p, sys.stdout)
" "$inventory_root" "$ansible_cfg"
