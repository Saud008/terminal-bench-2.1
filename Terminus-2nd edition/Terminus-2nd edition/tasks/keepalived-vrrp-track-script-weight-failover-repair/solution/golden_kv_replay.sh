#!/usr/bin/env bash
# Replay idempotency — skip duplicate event_id.

kv_replay_should_skip() {
  local event_id="$1"
  local staging_path="$2"
  python3 - "${event_id}" "${staging_path}" <<'PY'
import json, sys
eid, path = sys.argv[1], sys.argv[2]
staging = json.load(open(path, encoding="utf-8"))
print("1" if eid in staging.get("applied_event_ids", []) else "0")
PY
}

kv_replay_mark_applied() {
  local event_id="$1"
  local staging_path="$2"
  python3 - "${event_id}" "${staging_path}" <<'PY'
import json, sys
eid, path = sys.argv[1], sys.argv[2]
staging = json.load(open(path, encoding="utf-8"))
if eid not in staging.setdefault("applied_event_ids", []):
    staging["applied_event_ids"].append(eid)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
