#!/usr/bin/env bash
# Parse and validate Ansible facts JSONL streams.
set -euo pipefail

jsonl_line_count() {
  local jsonl="$1"
  grep -cve '^[[:space:]]*$' "${jsonl}" || true
}

validate_record() {
  local line="$1"
  python3 - "${line}" <<'PY'
import json, sys, re
line = sys.argv[1]
try:
    obj = json.loads(line)
except json.JSONDecodeError:
    raise SystemExit("invalid json")
for key in ("inventory_uuid", "hostname", "collected_at", "facts"):
    if key not in obj:
        raise SystemExit(f"missing {key}")
if not isinstance(obj["facts"], dict):
    raise SystemExit("facts must be object")
ts = obj["collected_at"]
if not isinstance(ts, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts):
    raise SystemExit("bad collected_at")
PY
}

jsonl_record_host_key() {
  local line="$1"
  python3 -c 'import json,sys; print(json.loads(sys.argv[1])["hostname"])' "${line}"
}

jsonl_record_inventory_uuid() {
  local line="$1"
  python3 -c 'import json,sys; print(json.loads(sys.argv[1])["inventory_uuid"])' "${line}"
}

jsonl_record_hostname() {
  local line="$1"
  python3 -c 'import json,sys; print(json.loads(sys.argv[1])["hostname"])' "${line}"
}

jsonl_record_collected_at() {
  local line="$1"
  python3 -c 'import json,sys; print(json.loads(sys.argv[1])["collected_at"])' "${line}"
}

jsonl_each_fact() {
  local line="$1"
  python3 - "${line}" <<'PY'
import json, sys
obj = json.loads(sys.argv[1])
for k, v in sorted(obj["facts"].items()):
    print(f"{k}\t{json.dumps(v, separators=(',', ':'))}")
PY
}
