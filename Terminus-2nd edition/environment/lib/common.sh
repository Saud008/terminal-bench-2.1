#!/usr/bin/env bash

SPAM_SPOOL="/app/work/spool/spam"
VIRUS_SPOOL="/app/work/spool/virus"
RELEASED_SPAM="/app/work/released/spam"
RELEASED_VIRUS="/app/work/released/virus"
LEDGER_PATH="/app/work/ledger.json"
MANIFEST_PATH="/app/state/spool-manifest.json"
STAGING_PATH="/app/state/release-staging.json"
EPOCH_PATH="/app/state/release-epoch.json"
STATE_PATH="/app/work/session-state.json"
SEAL_PATH="/app/state/prepare-seal.json"
CUSTODY_JOURNAL_PATH="/app/state/custody-journal.jsonl"

json_get() {
  local file="$1"
  local key="$2"
  python3 - "$file" "$key" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
key = sys.argv[2]
cur = doc
for part in key.split("."):
    if isinstance(cur, dict):
        cur = cur.get(part)
    else:
        cur = None
        break
if cur is None:
    sys.exit(1)
if isinstance(cur, bool):
    print("true" if cur else "false")
else:
    print(cur)
PY
}

msg_paths() {
  local root="$1"
  local qid="$2"
  MSG_EML="${root}/msg.${qid}.eml"
  MSG_META="${root}/msg.${qid}.meta.json"
}

spool_for_class() {
  local qclass="$1"
  if [[ "$qclass" == "spam" ]]; then
    SPOOL_DIR="$SPAM_SPOOL"
  else
    SPOOL_DIR="$VIRUS_SPOOL"
  fi
}

released_dir_for_class() {
  local qclass="$1"
  if [[ "$qclass" == "spam" ]]; then
    RELEASED_DIR="$RELEASED_SPAM"
  else
    RELEASED_DIR="$RELEASED_VIRUS"
  fi
}

list_pending_ids() {
  local root="$1"
  PENDING_IDS=()
  shopt -s nullglob
  for eml in "${root}"/msg.*.eml; do
    local base
    base="$(basename "$eml" .eml)"
    PENDING_IDS+=("${base#msg.}")
  done
  shopt -u nullglob
}
