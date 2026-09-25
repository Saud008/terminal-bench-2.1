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
mkdir -p "$(dirname "${staging}")"

python3 - "${workspace}" "${staging}" <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")
from audit.compliance_engine import ingest_workspace

ws = Path(sys.argv[1])
out = Path(sys.argv[2])
data = ingest_workspace(ws)
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

bash "${APP_ROOT}/lib/staging_commit.sh" "${workspace}" "${staging}"
exit 0
