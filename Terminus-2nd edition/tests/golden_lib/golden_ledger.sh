#!/usr/bin/env bash

init_ledger() {
  python3 - <<'PY'
import json
doc = {"next_sequence": 1, "entries": []}
with open("/app/work/ledger.json", "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

record_release_attempt() {
  local qid="$1"
  local qclass="$2"
  local status="$3"
  local queue_id="$4"
  python3 - "$qid" "$qclass" "$status" "$queue_id" <<'PY'
import json, os, sys
qid, qclass, status, queue_id = sys.argv[1:5]
path = "/app/work/ledger.json"
doc = {"next_sequence": 1, "entries": []}
if os.path.isfile(path):
    doc = json.load(open(path, encoding="utf-8"))
seq = None
if status == "released":
    seq = int(doc.get("next_sequence", 1))
    doc["next_sequence"] = seq + 1
row = {
    "quarantine_id": qid,
    "class": qclass,
    "status": status,
    "queue_id": queue_id or "",
}
if seq is not None:
    row["sequence"] = seq
doc.setdefault("entries", []).append(row)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

ledger_tail_sequence() {
  python3 - <<'PY'
import json, os
path = "/app/work/ledger.json"
if not os.path.isfile(path):
    print(0)
    raise SystemExit(0)
doc = json.load(open(path, encoding="utf-8"))
entries = doc.get("entries", [])
released = [e for e in entries if e.get("status") == "released" and "sequence" in e]
if not released:
    print(0)
else:
    print(max(int(e["sequence"]) for e in released))
PY
}
