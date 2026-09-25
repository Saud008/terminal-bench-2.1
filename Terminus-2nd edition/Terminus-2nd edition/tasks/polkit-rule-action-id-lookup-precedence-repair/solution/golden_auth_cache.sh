#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pk_cache_get() {
  local action_id="$1"
  local user="$2"
  local seat="$3"
  python3 - "$CACHE_PATH" "$action_id" "$user" "$seat" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
action_id, user, seat = sys.argv[2:5]
key = f"{action_id}|{user}|{seat}"
cache = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
print("1" if cache.get(key) else "0")
PY
}

pk_cache_set() {
  local action_id="$1"
  local user="$2"
  local seat="$3"
  python3 - "$CACHE_PATH" "$action_id" "$user" "$seat" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
action_id, user, seat = sys.argv[2:5]
key = f"{action_id}|{user}|{seat}"
cache = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
cache[key] = True
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(cache, sort_keys=True), encoding="utf-8")
PY
}
