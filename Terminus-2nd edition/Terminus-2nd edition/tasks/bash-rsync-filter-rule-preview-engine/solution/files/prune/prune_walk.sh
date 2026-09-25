#!/usr/bin/env bash
set -euo pipefail

should_prune_directory() {
  local dir_path="$1"
  local transfer="$2"
  local token="$3"
  python3 - <<'PY' "$dir_path" "$transfer" "$token"
import sys
path, transfer, _token = sys.argv[1], sys.argv[2], sys.argv[3]
is_dir = "." not in path.split("/")[-1]
print("true" if is_dir and transfer == "exclude" else "false")
PY
}
