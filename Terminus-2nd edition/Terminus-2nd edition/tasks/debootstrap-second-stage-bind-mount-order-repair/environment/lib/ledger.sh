#!/usr/bin/env bash

s2_append_ledger() {
  local staging="$1"
  python3 - "$staging" <<'PY'
import json
import os
import sys

staging_path = sys.argv[1]
staging = json.load(open(staging_path, encoding="utf-8"))
ledger_path = "/app/state/stage2-ledger.json"
try:
    ledger = json.load(open(ledger_path, encoding="utf-8"))
except FileNotFoundError:
    ledger = {"entries": []}
entry = {
    "sequence": len(ledger["entries"]) + 1,
    "seed": staging["seed"],
    "rootfs": staging["rootfs"],
    "staging_path": staging_path,
    "stage_binding": staging["stage_binding"],
}
ledger["entries"].append(entry)
os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
with open(ledger_path, "w", encoding="utf-8") as fh:
    json.dump(ledger, fh, indent=2)
    fh.write("\n")
PY
}
