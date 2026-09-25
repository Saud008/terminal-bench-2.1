#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/core/common.sh"
source "${APP_ROOT}/lib/time/exif_time.sh"
source "${APP_ROOT}/lib/lens/lens_match.sh"
source "${APP_ROOT}/lib/gap/frame_gap.sh"
source "${APP_ROOT}/lib/rig/rig_slot.sh"
source "${APP_ROOT}/lib/checker/checker_gate.sh"

lenses=""
checkerboard=""
while [ $# -gt 0 ]; do
  case "$1" in
    --lenses) lenses="$2"; shift 2 ;;
    --checkerboard) checkerboard="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${lenses}" ] && [ -n "${checkerboard}" ] || die "align requires --lenses and --checkerboard"
require_file "${STAGING_PATH}"
require_file "${lenses}"
require_file "${checkerboard}"

python3 - "${STAGING_PATH}" "${lenses}" "${checkerboard}" "${ALIGN_GEN_PATH}" "${REJECTED_PATH}" "${CAL_ERROR_LIMIT}" "${APP_ROOT}" <<'PY'
import json, os, subprocess, sys

staging_path, lenses, checker, align_out, rejected_out, limit_s, app_root = sys.argv[1:8]
limit = float(limit_s)

def bash_fn(lib, fn, *args):
    cmd = (
        f"set -euo pipefail; "
        f"source {app_root}/lib/core/common.sh; "
        f"source {app_root}/lib/{lib}; "
        + fn + " " + " ".join("'" + str(a).replace("'", "'\\''") + "'" for a in args)
    )
    return subprocess.check_output(["bash", "-c", cmd], text=True).strip()

staging = json.load(open(staging_path, encoding="utf-8"))
mount = staging["mount_path"]
captures = staging["captures"]
entries, rejected, accepted_for_gap = [], [], []
prev_gen = 0
if os.path.isfile(align_out):
    prev_gen = int(json.load(open(align_out, encoding="utf-8")).get("generation", 0))
generation = max(prev_gen + 1, 1)

for cap in captures:
    norm = int(bash_fn("time/exif_time.sh", "normalize_exif_ms", cap["timestamp_raw"], cap["timestamp_tz"]))
    gate = bash_fn("rig/rig_slot.sh", "validate_rig_slot", mount, cap["rig_slot"], cap["camera_serial"], cap["lens_id"])
    if gate != "ok":
        rejected.append({"capture_id": cap["capture_id"], "reason": gate})
        continue
    prof_raw = bash_fn("lens/lens_match.sh", "match_lens_profile", lenses, cap["lens_id"], norm)
    if not prof_raw:
        rejected.append({"capture_id": cap["capture_id"], "reason": "missing_lens_profile"})
        continue
    prof = json.loads(prof_raw)
    cal = bash_fn("checker/checker_gate.sh", "checker_gate", checker, cap["capture_id"], limit)
    if cal != "ok":
        rejected.append({"capture_id": cap["capture_id"], "reason": cal})
        continue
    row = {
        "capture_id": cap["capture_id"],
        "rig_slot": int(cap["rig_slot"]),
        "camera_serial": cap["camera_serial"],
        "lens_id": cap["lens_id"],
        "frame_index": int(cap["frame_index"]),
        "normalized_ms": norm,
        "profile_revision": prof.get("profile_revision", ""),
        "focal_mm": float(prof.get("focal_mm", 0)),
        "aligned": True,
    }
    entries.append(row)
    accepted_for_gap.append({"rig_slot": row["rig_slot"], "frame_index": row["frame_index"]})

missing = json.loads(bash_fn("gap/frame_gap.sh", "compute_missing_frames", mount, json.dumps(accepted_for_gap)))
entries.sort(key=lambda r: (r["normalized_ms"], r["capture_id"]))
align_doc = {
    "generation": generation,
    "staging_generation": staging["staging_generation"],
    "mount_sha256": staging["mount_sha256"],
    "entries": entries,
    "missing_frames": missing,
}
os.makedirs(os.path.dirname(align_out), exist_ok=True)
with open(align_out, "w", encoding="utf-8") as fh:
    json.dump(align_doc, fh, indent=2)
    fh.write("\n")
os.makedirs(os.path.dirname(rejected_out), exist_ok=True)
with open(rejected_out, "w", encoding="utf-8") as fh:
    for row in rejected:
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")
PY
