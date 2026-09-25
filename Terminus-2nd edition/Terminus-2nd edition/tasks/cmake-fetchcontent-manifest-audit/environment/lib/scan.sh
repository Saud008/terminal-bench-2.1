#!/usr/bin/env bash
# Install prefix scan (broken: closure module root-only; no hash snapshot gate).

# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/fetch_closure.sh"

HASH_SNAPSHOT="/app/state/hash-audit-snapshot.json"

scan_install_manifest() {
  local tree_json="$1"
  local prefix="$2"
  local out="$3"

  local artifacts=()
  local path kind sha
  while IFS= read -r -d '' f; do
    path="${f#${prefix}/}"
    if [[ -L "$f" ]]; then
      kind="symlink"
      sha="-"
    else
      kind="file"
      sha=$(sha256sum "$f" | awk '{print $1}')
    fi
    artifacts+=("{\"path\":\"${path}\",\"kind\":\"${kind}\",\"sha256\":\"${sha}\"}")
  done < <(find "$prefix" -type f -print0 | sort -z)

  local fetch_deps
  fetch_deps=$(fetch_collect_names "$tree_json")

  {
    echo '{'
    echo "  \"prefix\": \"${prefix}\","
    echo '  "artifacts": ['
    local i=0
    for line in "${artifacts[@]}"; do
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
