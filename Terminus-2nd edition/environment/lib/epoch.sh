#!/usr/bin/env bash
# Scaffold: implement per /app/docs/epoch-schema.md

bump_release_epoch() {
  python3 - <<'PY'
import json
from pathlib import Path
path = Path("/app/state/release-epoch.json")
path.parent.mkdir(parents=True, exist_ok=True)
# Always writes epoch 1 and ignores any prior file.
doc = {"epoch": 1}
path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

read_release_epoch() {
  echo 1
}
