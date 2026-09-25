#!/usr/bin/env bash
set -euo pipefail

compute_captures_digest() {
  local exif_jsonl="$1"
  python3 - "$exif_jsonl" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone

def norm_ms(raw, tz):
    dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000) - int(tz) * 60000

rows = []
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if line:
        rows.append(json.loads(line))
rows.sort(key=lambda r: (norm_ms(r["timestamp_raw"], r["timestamp_tz"]), r["capture_id"]))
body = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)
print(hashlib.sha256(body.encode()).hexdigest())
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
