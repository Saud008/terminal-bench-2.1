#!/usr/bin/env bash
# Publish conform atlas from sealed snapshot only.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
SEALED_FILE="${STATE_DIR}/edl-conform-sealed.json"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/seal_policy.sh"

usage() {
  echo "usage: conform_publish.sh --bundle <bundle_id> --output <path>" >&2
  exit 2
}

BUNDLE_ID=""
OUTPUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle) BUNDLE_ID="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "${BUNDLE_ID}" && -n "${OUTPUT}" ]] || usage

[[ -f "${SEALED_FILE}" ]] || exit 3

readarray -t META < <(python3 - "${SEALED_FILE}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(d["bundle_id"])
print(d.get("seal_digest", ""))
PY
)
if [[ "${META[0]}" != "${BUNDLE_ID}" ]]; then
  exit 3
fi

if emit_reopens_bundle; then
  python3 - "${SEALED_FILE}" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
data.setdefault("diagnostics", []).append(
    {"category": "publish_reopen_trap", "detail": "bundle paths reopened during publish"}
)
json.dump(data, open(path, "w", encoding="utf-8"), sort_keys=True, indent=2)
open(path, "a", encoding="utf-8").write("\n")
PY
fi

mkdir -p "$(dirname "${OUTPUT}")"
python3 - "${OUTPUT}" "${SEALED_FILE}" <<'PY'
import json, sys
from pathlib import Path
out, sealed_path = sys.argv[1:3]
sealed_doc = json.load(open(sealed_path, encoding="utf-8"))
atlas = {
    "bundle_id": sealed_doc["bundle_id"],
    "seal_digest": sealed_doc["seal_digest"],
    "edit_count": len(sealed_doc.get("edits", [])),
    "diagnostic_count": len(sealed_doc.get("diagnostics", [])),
    "diagnostics": sealed_doc.get("diagnostics", []),
    "edits": sealed_doc.get("edits", []),
}
Path(out).write_text(json.dumps(atlas, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY

exit 0
