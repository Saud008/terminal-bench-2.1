#!/usr/bin/env bash
# Convert HH:MM:SS:FF to frame index using bundle timecode map flags.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
# shellcheck source=/dev/null
source "${APP_ROOT}/lib/tc_policy.sh"

tc_to_frames() {
  local tc="$1"
  local fps="$2"
  local drop_frame="$3"
  local h m s f total_minutes frames drop_per_minute
  tc="${tc//$'\r'/}"
  IFS=: read -r h m s f <<< "${tc}"
  h=$((10#${h}))
  m=$((10#${m}))
  s=$((10#${s}))
  f=$((10#${f}))

  frames=$(( (h * 3600 + m * 60 + s) * fps + f ))

  if [[ "${drop_frame}" == "true" || "${drop_frame}" == "1" ]]; then
    if [[ "${DROP_FRAME_LINEAR}" -eq 1 ]]; then
      printf '%s\n' "${frames}"
      return 0
    fi
    drop_per_minute=2
    total_minutes=$(( h * 60 + m ))
    frames=$(( frames - drop_per_minute * (total_minutes - total_minutes / 10) ))
  fi
  printf '%s\n' "${frames}"
}

frames_to_tc() {
  local frames="$1"
  local fps="$2"
  local drop_frame="$3"
  local h m s f rem total_minutes drop_per_minute
  rem="${frames}"

  if [[ "${drop_frame}" == "true" || "${drop_frame}" == "1" ]]; then
    if [[ "${DROP_FRAME_LINEAR}" -eq 0 ]]; then
      drop_per_minute=2
      total_minutes=$(( rem / (fps * 60) ))
      rem=$(( rem + drop_per_minute * (total_minutes - total_minutes / 10) ))
    fi
  fi

  h=$(( rem / (fps * 3600) ))
  rem=$(( rem % (fps * 3600) ))
  m=$(( rem / (fps * 60) ))
  rem=$(( rem % (fps * 60) ))
  s=$(( rem / fps ))
  f=$(( rem % fps ))
  printf '%02d:%02d:%02d:%02d\n' "${h}" "${m}" "${s}" "${f}"
}
