#!/usr/bin/env bash

OI_APP_ROOT="${OI_APP_ROOT:-/app}"
OI_STATE_DIR="${OI_STATE_DIR:-${OI_APP_ROOT}/state}"
OI_SYNC_RUN="${OI_SYNC_RUN:-${OI_STATE_DIR}/sync-run.json}"

oi_write_sync_run() {
  local account="$1"
  local reference_epoch="$2"
  local synced_messages="$3"
  local synced_bytes="$4"
  local dry_run="$5"
  mkdir -p "${OI_STATE_DIR}"
  python3 - "$account" "$reference_epoch" "$synced_messages" "$synced_bytes" "$dry_run" "$OI_SYNC_RUN" <<'PY'
import json
import sys
from pathlib import Path

account, ref, msgs, byts, dry, out = sys.argv[1:7]
doc = {
    "schema": 1,
    "account": account,
    "reference_epoch": int(ref),
    "synced_messages": int(msgs),
    "synced_bytes": int(byts),
    "dry_run": dry.lower() == "true",
}
Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
