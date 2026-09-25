#!/usr/bin/env bash
# Decoy human-readable formatter — not used by export hot path.
set -euo pipefail

format_timer_summary() {
  local json_file="$1"
  python3 - "${json_file}" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"timer={doc.get('timer_name')} mode={doc.get('timer_mode')}")
PY
}
