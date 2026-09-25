#!/usr/bin/env bash

OI_APP_ROOT="${OI_APP_ROOT:-/app}"
OI_SNAPSHOT_PATH="${OI_SNAPSHOT_PATH:-${OI_APP_ROOT}/state/folder-snapshot.json}"

oi_publish_folder_snapshot() {
  local account="$1"
  local folders_json="$2"
  python3 - "$account" "$folders_json" "$OI_SNAPSHOT_PATH" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

account, folders_json, out_path = sys.argv[1:4]
folders = json.loads(folders_json)
selected = sorted(f["name"] for f in folders if f.get("selected"))
payload = json.dumps(selected, separators=(",", ":")).encode("utf-8")
digest = hashlib.sha256(payload).hexdigest()
snapshot = {
    "schema": 1,
    "account": account,
    "folders": folders,
    "folder_digest": digest,
}
Path(out_path).parent.mkdir(parents=True, exist_ok=True)
Path(out_path).write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(out_path)
PY
}
