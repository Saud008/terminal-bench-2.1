#!/usr/bin/env bash

TSCN_APP_ROOT="${TSCN_APP_ROOT:-/app}"

tscn_lib_dir() {
  echo "${TSCN_APP_ROOT}/lib/tscn"
}

tscn_read_bytes() {
  local path="$1"
  [[ -f "${path}" ]] || { echo ""; return 0; }
  cat "${path}"
}

tscn_normalize_lf() {
  python3 - "$1" <<'PY'
import sys
text = sys.argv[1]
text = text.replace("\r\n", "\n").replace("\r", "\n")
print(text, end="")
PY
}

tscn_load_json() {
  local path="$1"
  python3 - "${path}" <<'PY'
import json
import sys
from pathlib import Path
print(json.dumps(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))))
PY
}

tscn_json_get() {
  local json="$1" key="$2"
  python3 - "${json}" "${key}" <<'PY'
import json, sys
obj = json.loads(sys.argv[1])
key = sys.argv[2]
print(json.dumps(obj[key]))
PY
}

tscn_write_export() {
  local export_path="$1" payload="$2"
  python3 - "${export_path}" "${payload}" <<'PY'
import json, sys
from pathlib import Path
export_path = Path(sys.argv[1])
payload = json.loads(sys.argv[2])
export_path.parent.mkdir(parents=True, exist_ok=True)
export_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
PY
}

tscn_file_mtime() {
  stat -c %Y "$1" 2>/dev/null || echo 0
}
