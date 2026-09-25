#!/usr/bin/env bash

parse_atq_epoch() {
  local path="$1"
  python3 - "$path" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    print("0")
    raise SystemExit
first = path.read_text(encoding="utf-8").splitlines()[0]
for token in first.split():
    if token.startswith("ATQ_EPOCH="):
        print(token.split("=", 1)[1])
        raise SystemExit
print("0")
PY
}

build_atq_lines() {
  python3 - "$SPOOL_DIR" <<'PY'
import json, sys
from pathlib import Path
spool = Path(sys.argv[1])
rows = []
for path in spool.iterdir():
    if not path.is_file():
        continue
    first = path.read_text(encoding="utf-8").splitlines()[0]
    atq = "0"
    batch = ""
    job = ""
    for token in first.split():
        if token.startswith("ATQ_EPOCH="):
            atq = token.split("=", 1)[1]
        elif token.startswith("BATCH="):
            batch = token.split("=", 1)[1]
        elif token.startswith("JOB="):
            job = token.split("=", 1)[1]
    rows.append({"name": path.name, "atq_epoch": int(atq), "batch": batch, "job": job})
rows.sort(key=lambda r: (r["atq_epoch"], r["name"]))
print(json.dumps(rows))
PY
}
