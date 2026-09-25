#!/usr/bin/env bash
# Scaffold: implement per /app/docs/ledger-schema.md

init_ledger() {
  python3 - <<'PY'
import json
with open("/app/work/ledger.json", "w", encoding="utf-8") as fh:
    json.dump({"next_sequence": 1, "entries": []}, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

record_release_attempt() {
  return 0
}

ledger_tail_sequence() {
  echo 0
}
