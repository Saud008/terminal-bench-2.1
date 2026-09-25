#!/usr/bin/env bash
# Install prefix scan (golden).

# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/fetch_closure.sh"

HASH_SNAPSHOT="/app/state/hash-audit-snapshot.json"

scan_install_manifest() {
  local tree_json="$1"
  local prefix="$2"
  local out="$3"

  if [[ ! -f "$HASH_SNAPSHOT" ]]; then
    echo "missing hash-audit snapshot: $HASH_SNAPSHOT" >&2
    return 2
  fi
  python3 - <<PY
import json, sys
snap = json.load(open("${HASH_SNAPSHOT}", encoding="utf-8"))
if snap.get("version") != 1 or snap.get("failures"):
    sys.exit(2)
PY
  || {
    echo "hash-audit snapshot gate failed" >&2
    return 2
  }

  local artifacts=()
  local path kind sha
  while IFS= read -r -d '' f; do
    path="${f#${prefix}/}"
    if [[ -L "$f" ]]; then
      kind="symlink"
      sha="-"
    elif [[ -f "$f" ]]; then
      kind="file"
      sha=$(sha256sum "$f" | awk '{print $1}')
    else
      continue
    fi
    artifacts+=("{\"path\":\"${path}\",\"kind\":\"${kind}\",\"sha256\":\"${sha}\"}")
  done < <(find "$prefix" \( -type f -o -type l \) -print0 | sort -z)

  local fetch_deps
  fetch_deps=$(fetch_collect_names "$tree_json")

  mkdir -p "$(dirname "$out")"
  {
    echo '{'
    echo "  \"prefix\": \"${prefix}\","
    echo '  "artifacts": ['
    local i=0
    for line in "${artifacts[@]+"${artifacts[@]}"}"; do
      [[ $i -gt 0 ]] && echo ','
      echo -n "    ${line}"
      i=$((i + 1))
    done
    echo
    echo '  ],'
    echo "  \"fetch_deps\": ${fetch_deps},"
    echo "  \"transitive_closure\": ${fetch_deps}"
    echo '}'
  } > "$out"
}
