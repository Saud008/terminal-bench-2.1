#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
exec python3 - "$@" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/app/lib")))
import inventory_engine as eng

eng.staging_policy.EXPORT_REOPEN = True
tree_id = ""
output = ""
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--tree" and i + 1 < len(args):
        tree_id = args[i + 1]
        i += 2
    elif args[i] == "--output" and i + 1 < len(args):
        output = args[i + 1]
        i += 2
    else:
        i += 1
raise SystemExit(eng.cmd_emit(tree_id, output))
PY
