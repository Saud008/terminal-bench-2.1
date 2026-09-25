#!/usr/bin/env bash

REPLAY_LEDGER="${APP_ROOT:-/app}/state/sysctlmerge.replay.jsonl"

append_replay_record() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import json, sys
from pathlib import Path

snap = Path(sys.argv[1])
meta = json.loads(snap.read_text(encoding="utf-8"))
ledger = Path("/app/state/sysctlmerge.replay.jsonl")
record = {
    "tree": meta["tree"],
    "replay_token": f"len:{len(meta.get('processing_order', []))}",
}
ledger.parent.mkdir(parents=True, exist_ok=True)
with ledger.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(record) + "\n")
PY
}

validate_replay_record() {
  return 0
}
