#!/usr/bin/env bash
# Flattened stack staging between parse and execute.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pamreplay_stage_path() {
  echo "${PAMREPLAY_APP_ROOT}/work/replay.staging.json"
}

pamreplay_stage_reset() {
  :
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
incoming = json.loads(sys.argv[2])

if path.is_file():
    prior = json.loads(path.read_text(encoding="utf-8"))
    merged_entries = list(prior.get("entries", [])) + list(incoming.get("entries", []))
else:
    merged_entries = list(incoming.get("entries", []))

by_phase: dict[str, list] = {}
for entry in merged_entries:
    phase = entry.get("phase", "")
    by_phase.setdefault(phase, []).append(entry)

ordered: list = []
for phase in sorted(by_phase.keys()):
    phase_entries = sorted(by_phase[phase], key=lambda e: e.get("module", ""))
    ordered.extend(phase_entries)

doc = {
    "stack_id": incoming.get("stack_id", ""),
    "service": incoming.get("service", ""),
    "entries": ordered,
}
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
