#!/usr/bin/env bash
# Broken export-only: skips captures_digest validation; manifest_digest pending
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/core/common.sh"

require_file "${STAGING_PATH}"
require_file "${ALIGN_GEN_PATH}"

python3 - "${STAGING_PATH}" "${ALIGN_GEN_PATH}" "${BUNDLE_PATH}" <<'PY'
import json, sys
staging = json.load(open(sys.argv[1], encoding="utf-8"))
align = json.load(open(sys.argv[2], encoding="utf-8"))
if int(align.get("generation", 0)) < 1:
    raise SystemExit("align_generation zero")
bundle = {
    "align_generation": align["generation"],
    "staging_generation": align["staging_generation"],
    "entries": align["entries"],
    "missing_frames": align["missing_frames"],
    "manifest_digest": "pending",
}
out = sys.argv[3]
import os
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as fh:
    json.dump(bundle, fh, indent=2)
    fh.write("\n")
PY
