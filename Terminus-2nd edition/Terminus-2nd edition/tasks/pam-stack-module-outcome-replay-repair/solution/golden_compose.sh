#!/usr/bin/env bash
# Flattened stack compose artifact between flatten and staging.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pamreplay_compose_path() {
  echo "${PAMREPLAY_APP_ROOT}/work/replay.compose.json"
}

pamreplay_compose_reset() {
  rm -f "$(pamreplay_compose_path)"
}

pamreplay_compose_write() {
  local flat_json="$1"
  local path
  path="$(pamreplay_compose_path)"
  mkdir -p "$(dirname "${path}")"
  python3 - "$path" "$flat_json" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
doc = json.loads(sys.argv[2])
path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
PY
}

pamreplay_compose_read() {
  local path
  path="$(pamreplay_compose_path)"
  if [[ ! -f "${path}" ]]; then
    echo "pamreplay: compose artifact missing at ${path}" >&2
    return 1
  fi
  cat "${path}"
}
