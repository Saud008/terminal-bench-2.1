#!/usr/bin/env bash

extract_quarantine_id() {
  local line="$1"
  PARSED_QID=""
  PARSED_QUEUE_ID=""
  PARSED_QID="$(python3 - "$line" <<'PY'
import re, sys
line = sys.argv[1]
m = re.search(r'Quarantine-ID:\s*([^\s,]+)', line)
if not m:
    sys.exit(1)
print(m.group(1))
PY
)"
  PARSED_QUEUE_ID="$(python3 - "$line" <<'PY'
import re, sys
line = sys.argv[1]
m = re.search(r'Queue-ID:\s*([^\s,]+)', line)
print(m.group(1) if m else "")
PY
)"
  [[ -n "$PARSED_QID" ]] || return 1
}
