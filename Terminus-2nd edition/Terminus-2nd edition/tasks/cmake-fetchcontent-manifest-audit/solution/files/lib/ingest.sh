#!/usr/bin/env bash
# Stage-1 CMake ingest (golden).

# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/normalize.sh"

INGEST_SNAPSHOT="/app/state/cmake-ingest-snapshot.json"
INGEST_ROOT=""
INGEST_FILES=()

_ingest_one() {
  local rel="$1"
  local abs="${INGEST_ROOT}/${rel}"
  local list_dir
  list_dir="$(cd "$(dirname "$abs")" && pwd)"
  local includes_raw=() subdirs_raw=()
  local line inc sub

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    if [[ "$line" =~ include[[:space:]]*\([[:space:]]*\"([^\"]+)\" ]]; then
      inc="${BASH_REMATCH[1]}"
      includes_raw+=("$(join_rel "$(dirname "$rel")" "$inc")")
    fi
    if [[ "$line" =~ add_subdirectory[[:space:]]*\([[:space:]]*\"?([^\"[:space:]()]+) ]]; then
      sub="${BASH_REMATCH[1]}"
      sub="${sub//\"/}"
      subdirs_raw+=("$(join_rel "$(dirname "$rel")" "$sub")")
    fi
  done < "$abs"

  local fetch_json
  fetch_json=$(python3 -c '
import json, re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = []
for line in text.splitlines():
    if "#" in line:
        line = line.split("#", 1)[0]
    lines.append(line)
blob = "\n".join(lines)
entries = []
for m in re.finditer(
    r"(?is)FetchContent_Declare\s*\(\s*([^\s()]+)\s*(.*?)(?=FetchContent_Declare\s*\(|\Z)",
    blob,
):
    name = m.group(1).strip()
    body = m.group(2)
    url_m = re.search(r"URL\s+file://[^\s)]+/([^\s)/]+\.tar\.gz)", body)
    hash_m = re.search(r"URL_HASH\s+SHA256=([0-9a-fA-F]+)", body)
    entries.append({
        "name": name,
        "url": url_m.group(1) if url_m else "",
        "url_hash": hash_m.group(1).lower() if hash_m else "",
    })
print(json.dumps(entries))
' "$abs")

  local inc_json sub_json
  inc_json=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${includes_raw[@]+"${includes_raw[@]}"}")
  sub_json=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${subdirs_raw[@]+"${subdirs_raw[@]}"}")
  INGEST_FILES+=("${rel}"$'\t'"${list_dir}"$'\t'"${inc_json}"$'\t'"${sub_json}"$'\t'"${fetch_json}")
}

ingest_cmake_tree() {
  local root="$1"
  INGEST_ROOT="$(cd "$root" && pwd)"
  INGEST_FILES=()
  local -a queue=("CMakeLists.txt")
  local -A visited=()
  local rel entry subdirs_json sub sub_rel

  while [[ ${#queue[@]} -gt 0 ]]; do
    rel="${queue[0]}"
    queue=("${queue[@]:1}")
    [[ -n "${visited[$rel]+x}" ]] && continue
    visited[$rel]=1
    [[ -f "${INGEST_ROOT}/${rel}" ]] || continue
    _ingest_one "$rel"
    entry="${INGEST_FILES[-1]}"
    subdirs_json=$(printf '%s' "$entry" | cut -f4)
    while IFS= read -r sub; do
      [[ -z "$sub" ]] && continue
      sub_rel="${sub}/CMakeLists.txt"
      queue+=("$sub_rel")
    done < <(python3 -c 'import json,sys
for s in sorted(set(json.loads(sys.argv[1]))):
    print(s)' "$subdirs_json")
  done
}

write_ingest_snapshot() {
  local out="${1:-$INGEST_SNAPSHOT}"
  mkdir -p "$(dirname "$out")"
  local tmp
  tmp=$(mktemp)
  {
    echo '['
    local first=1 entry
    for entry in "${INGEST_FILES[@]+"${INGEST_FILES[@]}"}"; do
      [[ $first -eq 0 ]] && echo ','
      first=0
      python3 -c '
import json, sys
rel, list_dir, incs, subs, fetch = sys.argv[1:6]
print(json.dumps({
    "path": rel,
    "list_dir": list_dir,
    "includes_raw": json.loads(incs),
    "subdirs_raw": json.loads(subs),
    "fetchcontent": json.loads(fetch),
}))
' "$(printf '%s' "$entry" | cut -f1)" \
        "$(printf '%s' "$entry" | cut -f2)" \
        "$(printf '%s' "$entry" | cut -f3)" \
        "$(printf '%s' "$entry" | cut -f4)" \
        "$(printf '%s' "$entry" | cut -f5-)"
    done
    echo
    echo ']'
  } > "$tmp"

  python3 -c '
import json, sys
from pathlib import Path
files = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = {
    "version": 1,
    "root": sys.argv[2],
    "files": files,
}
Path(sys.argv[3]).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
' "$tmp" "$INGEST_ROOT" "$out"
  rm -f "$tmp"
}
