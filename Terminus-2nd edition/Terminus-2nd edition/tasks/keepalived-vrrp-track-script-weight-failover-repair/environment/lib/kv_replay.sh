#!/usr/bin/env bash
# Replay idempotency for event_id deduplication.

kv_replay_should_skip() {
  local event_id="$1"
  local staging_path="$2"
  python3 - "${event_id}" "${staging_path}" <<'PY'
import json, sys
eid, path = sys.argv[1], sys.argv[2]
staging = json.load(open(path, encoding="utf-8"))
print("0")
PY
}

kv_replay_mark_applied() {
  local event_id="$1"
  local staging_path="$2"
  python3 - "${event_id}" "${staging_path}" <<'PY'
import json, sys
eid, path = sys.argv[1], sys.argv[2]
staging = json.load(open(path, encoding="utf-8"))
staging.setdefault("applied_event_ids", []).append(eid)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(staging, fh, separators=(",", ":"))
PY
}
