#!/usr/bin/env bash
set -euo pipefail

classify_delete_risk() {
  local path="$1"
  local transfer="$2"
  local parsed_json="$3"
  local receiver_json="$4"
  local sender_json="$5"
  python3 - <<'PY' "$path" "$transfer" "$parsed_json" "$receiver_json" "$sender_json"
import json, fnmatch, sys

def matches(path, pattern):
    anchored = False
    if pattern.startswith("/"):
        anchored = True
        pattern = pattern[1:]
    if pattern.endswith("/**"):
        base = pattern[:-3]
        if path == base or path.startswith(base + "/"):
            return True
    if anchored:
        return fnmatch.fnmatch(path, pattern)
    leaf = path.split("/")[-1]
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(leaf, pattern)

path, transfer = sys.argv[1], sys.argv[2]
parsed = json.loads(sys.argv[3])
receiver = set(json.loads(sys.argv[4]))
sender = set(json.loads(sys.argv[5]))
if path not in receiver:
    print("none")
elif any(row["token"] == "P" and matches(path, row["pattern"]) for row in parsed):
    print("protected")
elif path not in sender and any(row["token"] == "R" and matches(path, row["pattern"]) for row in parsed):
    print("candidate")
elif path not in sender and transfer == "exclude":
    print("candidate")
else:
    print("none")
PY
}
