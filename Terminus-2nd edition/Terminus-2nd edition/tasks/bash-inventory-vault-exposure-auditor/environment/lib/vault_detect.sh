#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
value="$1"
python3 -c "
import sys
sys.path.insert(0,'${APP_ROOT}/lib')
from inventory_engine import is_vault_value
print('vault' if is_vault_value(sys.argv[1]) else 'plain')
" "$value"
