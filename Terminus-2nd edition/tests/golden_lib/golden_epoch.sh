#!/usr/bin/env bash

bump_release_epoch() {
  python3 - <<'PY'
import json
from pathlib import Path

path = Path("/app/state/release-epoch.json")
path.parent.mkdir(parents=True, exist_ok=True)
prev = 0
if path.is_file():
    try:
        prev = int(json.loads(path.read_text(encoding="utf-8")).get("epoch", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        prev = 0
doc = {"epoch": prev + 1}
path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

read_release_epoch() {
  python3 - <<'PY'
import json
from pathlib import Path
path = Path("/app/state/release-epoch.json")
if not path.is_file():
    print(0)
    raise SystemExit(0)
try:
    print(int(json.loads(path.read_text(encoding="utf-8")).get("epoch", 0)))
except (json.JSONDecodeError, TypeError, ValueError):
    print(0)
PY
}
