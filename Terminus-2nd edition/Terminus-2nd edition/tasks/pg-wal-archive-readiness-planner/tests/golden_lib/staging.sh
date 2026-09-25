#!/usr/bin/env bash
# Write WAL archive staging snapshot JSON.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/label.sh"
source "${APP_ROOT}/lib/timeline.sh"
source "${APP_ROOT}/lib/partial.sh"
source "${APP_ROOT}/lib/digest.sh"

STAGING_VERSION=1

write_staging_snapshot() {
  local archive="$1"
  local staging_path="$2"
  local label_json
  label_json="$(parse_backup_label "${archive}")"
  local segments=()
  local timelines=()
  local partials
  partials="$(list_partial_files "${archive}")"
  local f
  for f in "${archive}"/*; do
    [[ -f "${f}" ]] || continue
    local base
    base="$(basename "${f}")"
    if [[ "${base}" == backup_label ]]; then
      continue
    fi
    if [[ "${base}" == *.history ]]; then
      timelines+=("$(parse_history_file "${f}")")
      continue
    fi
    if [[ "${base}" == *.partial ]]; then
      continue
    fi
    if [[ "${#base}" -eq 24 ]]; then
      segments+=("$(upper_hex "${base}")")
    fi
  done
  IFS=$'\n' segments=($(printf '%s\n' "${segments[@]:-}" | sort))
  unset IFS
  local tl_json="["
  local first=1
  local row
  for row in "${timelines[@]:-}"; do
    [[ -z "${row}" ]] && continue
    local tl="${row%%|*}"
    local parents="${row#*|}"
    [[ "${first}" -eq 1 ]] || tl_json+=","
    first=0
    tl_json+='{"timeline":'"${tl}"',"parents":['"${parents}"']}'
  done
  tl_json+="]"
  local partial_json="["
  first=1
  while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    [[ "${first}" -eq 1 ]] || partial_json+=","
    first=0
    partial_json+="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "${line}")"
  done <<< "${partials}"
  partial_json+="]"
  local seg_json
  seg_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${segments[@]:-}")"
  local digest_payload
  digest_payload="$(python3 - "${label_json}" "${seg_json}" "${tl_json}" <<'PY'
import json, sys
label = json.loads(sys.argv[1])
segments = json.loads(sys.argv[2])
timelines = json.loads(sys.argv[3])
print(json.dumps({
    "segments": segments,
    "timelines": timelines,
    "start_timeline": label["start_timeline"],
    "start_segment_file": label["start_segment_file"],
}, separators=(",", ":")))
PY
)"
  local digest
  digest="$(staging_digest "${digest_payload}")"
  python3 - "${staging_path}" "${archive}" "${label_json}" "${seg_json}" "${partial_json}" "${tl_json}" "${digest}" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
archive = sys.argv[2]
label = json.loads(sys.argv[3])
segments = json.loads(sys.argv[4])
partials = json.loads(sys.argv[5])
timelines = json.loads(sys.argv[6])
digest = sys.argv[7]
doc = {
    "staging_version": 1,
    "archive_root": archive,
    "start_time": label["start_time"],
    "start_timeline": label["start_timeline"],
    "start_segment_file": label["start_segment_file"],
    "segments_present": segments,
    "partial_files": partials,
    "timelines": timelines,
    "digest": digest,
}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
