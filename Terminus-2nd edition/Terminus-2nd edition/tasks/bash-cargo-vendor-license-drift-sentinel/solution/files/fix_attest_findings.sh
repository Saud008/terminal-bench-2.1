#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/cvls_paths.sh"

workspace=""
while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) workspace="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[ -n "${workspace}" ] && [ -d "${workspace}" ] || exit 2

staging="$(workspace_staging_path "${workspace}")"
[ -f "${staging}" ] || exit 2

python3 - "${staging}" <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")
from audit.compliance_engine import audit_staging

path = Path(sys.argv[1])
staging = json.loads(path.read_text(encoding="utf-8"))
if not staging.get("ingest_complete"):
    raise SystemExit(2)
audited = audit_staging(staging)
path.write_text(json.dumps(audited, indent=2) + "\n", encoding="utf-8")
PY

exit 0
