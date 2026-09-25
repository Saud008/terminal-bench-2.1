#!/usr/bin/env bash

: "${RELEASED_SPAM:=/app/work/released/spam}"
: "${RELEASED_VIRUS:=/app/work/released/virus}"


ledger_already_released() {
  local qid="$1"
  python3 - "$qid" <<'PY'
import json, os, sys
qid = sys.argv[1]
path = "/app/work/ledger.json"
if not os.path.isfile(path):
    sys.exit(1)
doc = json.load(open(path, encoding="utf-8"))
for row in doc.get("entries", []):
    if row.get("quarantine_id") == qid and row.get("status") == "released":
        sys.exit(0)
sys.exit(1)
PY
}

attempt_release() {
  local qid="$1"
  local qclass="$2"
  DUPLICATE_SKIPPED=0
  RELEASE_OK=0
  locate_message "$qid" "$qclass"
  if [[ -f "$MSG_EML" ]]; then
    released_dir_for_class "$qclass"
    mkdir -p "$RELEASED_DIR"
    mv -f "$MSG_EML" "${RELEASED_DIR}/msg.${qid}.eml"
    if [[ -f "$MSG_META" ]]; then
      mv -f "$MSG_META" "${RELEASED_DIR}/msg.${qid}.meta.json"
    fi
    RELEASE_OK=1
    return 0
  fi
  RELEASE_OK=0
  return 1
}
