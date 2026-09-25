#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/core/common.sh"

require_file "${STAGING_PATH}"
require_file "${ALIGN_GEN_PATH}"

python3 - "${STAGING_PATH}" "${ALIGN_GEN_PATH}" "${BUNDLE_PATH}" "${APP_ROOT}" <<'PY'
import hashlib, json, os, subprocess, sys
from datetime import datetime, timezone

staging_path, align_path, out, app_root = sys.argv[1:5]
staging = json.load(open(staging_path, encoding="utf-8"))
align = json.load(open(align_path, encoding="utf-8"))
if int(align.get("generation", 0)) < 1:
    raise SystemExit("align_generation zero")

def compute_digest(exif_path):
    rows = staging["captures"]
    def norm_ms(raw, tz):
        dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000) - int(tz) * 60000
    ordered = sorted(rows, key=lambda r: (norm_ms(r["timestamp_raw"], r["timestamp_tz"]), r["capture_id"]))
    body = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in ordered)
    return hashlib.sha256(body.encode()).hexdigest()

if compute_digest("") != staging["captures_digest"]:
    raise SystemExit("captures_digest mismatch")

def norm_json(v):
    if isinstance(v, float) and v == int(v):
        return int(v)
    if isinstance(v, dict):
        return {k: norm_json(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return [norm_json(x) for x in v]
    return v

bundle = {
    "align_generation": align["generation"],
    "staging_generation": align["staging_generation"],
    "entries": align["entries"],
    "missing_frames": align["missing_frames"],
}
payload = norm_json(bundle)
raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
bundle["manifest_digest"] = hashlib.sha256(raw.encode()).hexdigest()
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as fh:
    json.dump(bundle, fh, indent=2)
    fh.write("\n")
PY
