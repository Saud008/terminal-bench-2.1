#!/usr/bin/env bash
# Stage bundle manifest into sealed /app/state/edl-conform-sealed.json
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
SEALED_FILE="${STATE_DIR}/edl-conform-sealed.json"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_convert.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/reel_alias.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/handle_math.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/offline_media_ledger.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/seal_policy.sh"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_map_validate.sh"

usage() {
  echo "usage: conform_stage.sh --bundle <manifest.json>" >&2
  exit 2
}

BUNDLE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle) BUNDLE="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "${BUNDLE}" && -f "${BUNDLE}" ]] || exit 2

readarray -t BUNDLE_META < <(python3 - "${BUNDLE}" <<'PY'
import json, hashlib, sys
from pathlib import Path
p = Path(sys.argv[1]).resolve()
data = json.loads(p.read_text(encoding="utf-8"))
root = p.parent
parts = [p.read_bytes()]
for rel in sorted(data.get("fingerprint_files", [])):
    fp = root / rel
    if fp.is_file():
        parts.append(fp.read_bytes())
fp = hashlib.sha256(b"".join(parts)).hexdigest()
for key in ("bundle_id", "edl", "sources", "aliases", "missing", "tc_map"):
    val = data[key]
    if key == "bundle_id":
        print(val)
        continue
    path = Path(val)
    if not path.is_absolute():
        path = (root / val).resolve()
    print(str(path))
print(fp)
PY
)

BUNDLE_ID="${BUNDLE_META[0]}"
EDL_PATH="${BUNDLE_META[1]}"
SOURCES_PATH="${BUNDLE_META[2]}"
ALIASES_PATH="${BUNDLE_META[3]}"
MISSING_PATH="${BUNDLE_META[4]}"
TC_MAP_PATH="${BUNDLE_META[5]}"
FINGERPRINT="${BUNDLE_META[6]}"

validate_tc_map_header "${EDL_PATH}" "${TC_MAP_PATH}" || true

readarray -t TC_META < <(python3 - "${TC_MAP_PATH}" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
print(m.get("fps", 30))
print("true" if m.get("drop_frame") else "false")
print(m.get("pulldown", "none"))
PY
)
FPS="${TC_META[0]}"
DROP_FRAME="${TC_META[1]}"
PULLDOWN="${TC_META[2]}"

mkdir -p "${STATE_DIR}"
TMP_EDITS="${STATE_DIR}/.edits.jsonl"
TMP_DIAG="${STATE_DIR}/.diagnostics.jsonl"
: > "${TMP_EDITS}"
: > "${TMP_DIAG}"

declare -A SOURCE_FRAMES
while IFS=$'\t' read -r reel frames; do
  SOURCE_FRAMES["${reel}"]="${frames}"
done < <(python3 - "${SOURCES_PATH}" <<'PY'
import json, sys
for row in json.load(open(sys.argv[1], encoding="utf-8"))["reels"]:
    print(f"{row['reel']}\t{row['frame_count']}")
PY
)

while IFS=$'\t' read -r edit reel track trans rec_in rec_out src_in src_out; do
  [[ -z "${edit}" ]] && continue
  resolved="$(resolve_reel "${reel}" "${ALIASES_PATH}")"
  rec_in_f="$(tc_to_frames "${rec_in}" "${FPS}" "${DROP_FRAME}")"
  rec_out_f="$(tc_to_frames "${rec_out}" "${FPS}" "${DROP_FRAME}")"
  src_in_f="$(tc_to_frames "${src_in}" "${FPS}" "${DROP_FRAME}")"
  src_out_f="$(tc_to_frames "${src_out}" "${FPS}" "${DROP_FRAME}")"
  rec_span=$(( rec_out_f - rec_in_f ))
  src_span=$(( src_out_f - src_in_f ))
  handle_budget="$(handle_frame_budget "${src_in}" "${src_out}" "${FPS}" "${PULLDOWN}")"

  python3 - >> "${TMP_EDITS}" <<PY
import json
print(json.dumps({
  "edit": "${edit}",
  "reel": "${reel}",
  "resolved_reel": "${resolved}",
  "rec_in": "${rec_in}",
  "rec_out": "${rec_out}",
  "src_in": "${src_in}",
  "src_out": "${src_out}",
  "rec_in_frames": ${rec_in_f},
  "rec_out_frames": ${rec_out_f},
  "src_in_frames": ${src_in_f},
  "src_out_frames": ${src_out_f},
  "rec_span_frames": ${rec_span},
  "src_span_frames": ${src_span},
  "handle_budget_frames": int("${handle_budget}"),
}, sort_keys=True))
PY

  if [[ -z "${SOURCE_FRAMES[${resolved}]+x}" ]]; then
    if ! ledger_contains "${reel}" "${MISSING_PATH}" "${ALIASES_PATH}"; then
      python3 - >> "${TMP_DIAG}" <<PY
import json
print(json.dumps({"category":"alias_orphan","edit":"${edit}","reel":"${reel}","resolved_reel":"${resolved}"}, sort_keys=True))
PY
    fi
  fi

  if [[ "${rec_span}" -ne "${src_span}" ]]; then
    python3 - >> "${TMP_DIAG}" <<PY
import json
print(json.dumps({"category":"df_span_drift","edit":"${edit}","reel":"${reel}","rec_span":${rec_span},"src_span":${src_span}}, sort_keys=True))
PY
  fi

  if [[ -n "${SOURCE_FRAMES[${resolved}]+x}" ]]; then
    avail="${SOURCE_FRAMES[${resolved}]}"
    if (( src_out_f > avail )); then
      python3 - >> "${TMP_DIAG}" <<PY
import json
print(json.dumps({"category":"handle_exceeds_reel","edit":"${edit}","reel":"${resolved}","src_out_frames":${src_out_f},"available_frames":${avail}}, sort_keys=True))
PY
    fi
  fi

  if ledger_contains "${reel}" "${MISSING_PATH}" "${ALIASES_PATH}"; then
    python3 - >> "${TMP_DIAG}" <<PY
import json
print(json.dumps({"category":"offline_media_note","edit":"${edit}","reel":"${reel}","resolved_reel":"${resolved}","suppressed":True}, sort_keys=True))
PY
  fi

  if [[ "${PULLDOWN}" == "23976" && "${handle_budget}" -ne "${src_span}" ]]; then
    python3 - >> "${TMP_DIAG}" <<PY
import json
print(json.dumps({"category":"telecine_pull_drift","edit":"${edit}","reel":"${reel}","handle_budget":int("${handle_budget}"),"src_span":${src_span}}, sort_keys=True))
PY
  fi
done < <(gawk -f "${APP_ROOT}/lib/edl_parse.awk" "${EDL_PATH}")

RUN_SEQ=0
RUN_FILE="${STATE_DIR}/run-seq.json"
if [[ -f "${RUN_FILE}" ]]; then
  readarray -t RUN_META < <(python3 - "${RUN_FILE}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(d.get("run_seq", 0))
print(d.get("last_bundle_fingerprint", ""))
print(d.get("bundle_id", ""))
PY
)
  if [[ "${RUN_META[1]}" == "${FINGERPRINT}" && "${RUN_META[2]}" == "${BUNDLE_ID}" ]]; then
    RUN_SEQ="${RUN_META[0]}"
  else
    RUN_SEQ=$(( RUN_META[0] + 1 ))
  fi
else
  RUN_SEQ=1
fi

python3 - "${SEALED_FILE}" "${TMP_EDITS}" "${TMP_DIAG}" "${BUNDLE_ID}" "${FINGERPRINT}" "${FPS}" "${DROP_FRAME}" "${PULLDOWN}" "${RUN_SEQ}" "${DIGEST_INCLUDES_FINDINGS}" <<'PY'
import hashlib, json, sys
from pathlib import Path
out, edits_path, diag_path, bundle_id, fingerprint, fps, drop_frame, pulldown, run_seq, include_diag = sys.argv[1:11]
edits = [json.loads(line) for line in Path(edits_path).read_text(encoding="utf-8").splitlines() if line.strip()]
diagnostics = [json.loads(line) for line in Path(diag_path).read_text(encoding="utf-8").splitlines() if line.strip()]
body = {"edits": edits}
if include_diag == "1":
    body["diagnostics"] = diagnostics
digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
sealed_doc = {
    "bundle_id": bundle_id,
    "bundle_fingerprint": fingerprint,
    "run_seq": int(run_seq),
    "tc_profile": {
        "fps": int(fps),
        "drop_frame": drop_frame == "true",
        "pulldown": pulldown,
    },
    "edits": edits,
    "diagnostics": diagnostics,
    "seal_digest": digest,
}
Path(out).write_text(json.dumps(sealed_doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY

rm -f "${TMP_EDITS}" "${TMP_DIAG}"

python3 - > "${RUN_FILE}" <<PY
import json
print(json.dumps({
  "run_seq": int("${RUN_SEQ}"),
  "last_bundle_fingerprint": "${FINGERPRINT}",
  "bundle_id": "${BUNDLE_ID}",
}, sort_keys=True, indent=2))
PY

exit 0
