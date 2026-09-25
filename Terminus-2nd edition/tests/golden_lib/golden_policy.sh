#!/usr/bin/env bash

expected_hold_token() {
  local seed="$1"
  local qid="$2"
  printf '%s' "${seed}:${qid}" | sha256sum | awk '{print substr($1,1,12)}'
}

check_release_policy() {
  local qid="$1"
  local qclass="$2"
  local seed="$3"
  POLICY_OK=1
  if declare -F locate_message >/dev/null 2>&1; then
    locate_message "$qid" "$qclass" || true
  fi
  local meta="${MSG_META:-}"
  if [[ -z "$meta" || ! -f "$meta" ]]; then
    for root in "${SPAM_SPOOL:-/app/work/spool/spam}" "${VIRUS_SPOOL:-/app/work/spool/virus}"; do
      if [[ -f "${root}/msg.${qid}.meta.json" ]]; then
        meta="${root}/msg.${qid}.meta.json"
        break
      fi
    done
  fi
  if [[ -z "$meta" || ! -f "$meta" ]]; then
    POLICY_OK=1
    return 0
  fi
  local expected
  expected="$(expected_hold_token "$seed" "$qid")"
  if python3 - "$meta" "$expected" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
if "hold_token" not in doc:
    raise SystemExit(0)
if str(doc["hold_token"]) != sys.argv[2]:
    raise SystemExit(1)
raise SystemExit(0)
PY
  then
    POLICY_OK=1
    return 0
  fi
  POLICY_OK=0
  return 1
}

compute_policy_digest() {
  POLICY_DIGEST="$(python3 <<'PY'
import hashlib, json
from pathlib import Path
manifest_path = Path("/app/state/spool-manifest.json")
lines = []
if manifest_path.is_file():
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in doc.get("messages", []):
        qid = row["quarantine_id"]
        sub = row.get("spool_subdir", row.get("stored_class", "spam"))
        meta = Path(f"/app/work/spool/{sub}/msg.{qid}.meta.json")
        if not meta.is_file():
            continue
        mdoc = json.loads(meta.read_text(encoding="utf-8"))
        if "hold_token" in mdoc:
            lines.append(f"{qid}:{mdoc['hold_token']}")
lines.sort()
if lines:
    print(hashlib.sha256("\n".join(lines).encode()).hexdigest(), end="")
else:
    print("", end="")
PY
)"
}
