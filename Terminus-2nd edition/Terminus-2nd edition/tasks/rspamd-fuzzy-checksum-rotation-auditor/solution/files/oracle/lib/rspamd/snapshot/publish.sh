#!/usr/bin/env bash

RF_APP_ROOT="${RF_APP_ROOT:-/app}"
RF_SNAPSHOT_PATH="${RF_SNAPSHOT_PATH:-${RF_APP_ROOT}/state/shingle-snapshot.json}"

rf_publish_shingle_snapshot() {
  local manifest_path="$1"
  local epoch_salt="$2"
  python3 - "$manifest_path" "$epoch_salt" "$RF_SNAPSHOT_PATH" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest, salt, out_path = sys.argv[1:4]
mails = []
for line in Path(manifest).read_text(encoding="utf-8").splitlines()[1:]:
    if not line.strip():
        continue
    mail_id, _eml = line.split("\t", 1)
    mails.append(mail_id)
payload = json.dumps(mails, separators=(",", ":")).encode("utf-8")
digest = hashlib.sha256(payload).hexdigest()
doc = {
    "schema": 1,
    "mails": mails,
    "mail_digest": digest,
    "epoch_salt": salt,
}
Path(out_path).parent.mkdir(parents=True, exist_ok=True)
Path(out_path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
