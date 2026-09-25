#!/usr/bin/env bash
# Parse track event JSONL into a normalized list file.

kv_ingest_events() {
  local input_path="$1"
  local out_path="$2"
  python3 - "${input_path}" "${out_path}" <<'PY'
import json, sys
inp, out = sys.argv[1], sys.argv[2]
events = []
for raw in open(inp, encoding="utf-8"):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    obj = json.loads(line)
    events.append({
        "event_id": str(obj["event_id"]),
        "ts": int(obj["ts"]),
        "track": str(obj["track"]),
        "status": str(obj["status"]),
        "exit_code": int(obj.get("exit_code", 0)),
    })
with open(out, "w", encoding="utf-8") as fh:
    json.dump(events, fh, separators=(",", ":"))
PY
}
