#!/usr/bin/env bash
# Flattened stack staging between parse and execute.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pamreplay_stage_path() {
  echo "${PAMREPLAY_APP_ROOT}/work/replay.staging.json"
}

pamreplay_stage_reset() {
  rm -f "$(pamreplay_stage_path)"
}

pamreplay_stage_write() {
  local flat_json="$1"
  local path
  path="$(pamreplay_stage_path)"
  mkdir -p "$(dirname "${path}")"
  python3 - "$path" "$flat_json" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
doc = json.loads(sys.argv[2])
path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
PY
}

pamreplay_stage_read() {
  local path
  path="$(pamreplay_stage_path)"
  if [[ ! -f "${path}" ]]; then
    echo "pamreplay: staging artifact missing at ${path}" >&2
    return 1
  fi
  cat "${path}"
}
