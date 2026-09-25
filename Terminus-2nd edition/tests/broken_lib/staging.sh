#!/usr/bin/env bash
# Scaffold: implement per /app/docs/release-staging.md

write_release_staging() {
  python3 - <<'PY'
import json
from pathlib import Path

doc = {
    "staging_written": True,
    "pending_in_spool": {"spam": [], "virus": []},
    "index": {},
}
Path("/app/state/release-staging.json").write_text(
    json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY
}
