#!/usr/bin/env bash
# Stage-2 tree export (golden: preserve fetchcontent declaration order).

INGEST_SNAPSHOT="/app/state/cmake-ingest-snapshot.json"
PARSE_PAYLOAD=""

export_cmake_tree() {
  local ingest_json="${1:-$INGEST_SNAPSHOT}"
  PARSE_PAYLOAD=$(python3 - <<'PY' "$ingest_json"
import json, sys
from pathlib import Path

ingest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
files = []
for rec in ingest["files"]:
    includes = sorted(set(rec.get("includes_raw", [])))
    subdirs = sorted(set(rec.get("subdirs_raw", [])))
    # Preserve declaration order — do not sort fetchcontent by name.
    fetch = list(rec.get("fetchcontent", []))
    files.append(
        {
            "path": rec["path"],
            "list_dir": rec["list_dir"],
            "includes": includes,
            "subdirs": subdirs,
            "fetchcontent": fetch,
        }
    )
files.sort(key=lambda r: r["path"])
print(json.dumps({"root": ingest["root"], "files": files}, indent=2))
PY
)
}

write_tree_json() {
  local out="$1"
  mkdir -p "$(dirname "$out")"
  printf '%s\n' "$PARSE_PAYLOAD" > "$out"
}
