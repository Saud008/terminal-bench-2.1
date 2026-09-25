#!/usr/bin/env bash
set -euo pipefail

# Broken digest: sorts by capture_id only and uses fnv-style hash
compute_captures_digest() {
  local exif_jsonl="$1"
  python3 - "$exif_jsonl" <<'PY'
import json, sys
rows = []
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if line:
        rows.append(json.loads(line))
rows.sort(key=lambda r: r["capture_id"])
h = 1469598103934665603
for row in rows:
    for b in json.dumps(row, separators=(",", ":")).encode():
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
print(f"{h:016x}")
PY
}

mount_sha256() {
  local mount_json="$1"
  python3 - "$mount_json" <<'PY'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PY
}

bump_staging_seq() {
  local seq_path="$1"
  local gen=0
  if [ -f "${seq_path}" ]; then
    gen="$(python3 - "${seq_path}" <<'PY'
import json, sys
print(int(json.load(open(sys.argv[1], encoding="utf-8")).get("staging_generation", 0)))
PY
)"
  fi
  gen=$((gen + 1))
  mkdir -p "$(dirname "${seq_path}")"
  python3 - "${seq_path}" "${gen}" <<'PY'
import json, sys
path, gen = sys.argv[1], int(sys.argv[2])
with open(path, "w", encoding="utf-8") as fh:
    json.dump({"staging_generation": gen}, fh, indent=2)
    fh.write("\n")
print(gen)
PY
}
