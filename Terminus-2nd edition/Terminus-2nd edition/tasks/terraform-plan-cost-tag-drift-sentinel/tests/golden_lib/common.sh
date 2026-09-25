#!/usr/bin/env bash
set -euo pipefail

die() {
  echo "tf-tag-sentinel: $*" >&2
  exit 1
}

file_sha256() {
  sha256sum "$1" | awk '{print $1}'
}

json_compact_digest() {
  python3 - "$1" <<'PY'
import hashlib, json, sys
from pathlib import Path
doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
payload = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(payload).hexdigest())
PY
}
