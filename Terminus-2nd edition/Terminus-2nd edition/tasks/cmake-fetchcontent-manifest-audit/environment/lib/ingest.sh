#!/usr/bin/env bash
# Stage-1 CMake ingest (broken: CMAKE_SOURCE_DIR includes, shallow subdirs).

# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/normalize.sh"

INGEST_SNAPSHOT="/app/state/cmake-ingest-snapshot.json"
INGEST_ROOT=""
INGEST_FILES=()

_ingest_one() {
  local rel="$1"
  local abs="${INGEST_ROOT}/${rel}"
  local list_dir
  list_dir="$(dirname "$abs")"
  local includes_raw=() subdirs_raw=() fetch_names=() fetch_urls=() fetch_hashes=()
  local line inc sub name

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    if [[ "$line" =~ include[[:space:]]*\([[:space:]]*\"([^\"]+)\" ]]; then
      inc="${BASH_REMATCH[1]}"
      includes_raw+=("$(join_rel "." "$inc")")
    fi
    if [[ "$line" =~ add_subdirectory[[:space:]]*\([[:space:]]*\"?([^\"[:space:]()]+) ]]; then
      sub="${BASH_REMATCH[1]}"
      sub="${sub//\"/}"
      subdirs_raw+=("$(join_rel "$(dirname "$rel")" "$sub")")
    fi
    if [[ "$line" =~ [Ff]etch[Cc]ontent_[Dd]eclare[[:space:]]*\([[:space:]]*([^[:space:]]+) ]]; then
      name="${BASH_REMATCH[1]}"
      fetch_names+=("$name")
      fetch_urls+=("")
      fetch_hashes+=("")
    fi
    if [[ "$line" =~ URL[[:space:]]+file://[^[:space:]]+/([^[:space:]]+\.tar\.gz) ]]; then
      fetch_urls+=("${BASH_REMATCH[1]}")
    fi
    if [[ "$line" =~ URL_HASH[[:space:]]+SHA256=([0-9a-fA-F]+) ]]; then
      fetch_hashes+=("${BASH_REMATCH[1]}")
    fi
  done < "$abs"

  INGEST_FILES+=("$rel|$list_dir|${includes_raw[*]}|${subdirs_raw[*]}|${fetch_names[*]}|${fetch_urls[*]}|${fetch_hashes[*]}")
}

ingest_cmake_tree() {
  local root="$1"
  INGEST_ROOT="$root"
  INGEST_FILES=()
  _ingest_one "CMakeLists.txt"
  local entry subdirs
  for entry in "${INGEST_FILES[@]}"; do
    IFS='|' read -r _ _ _ subdirs _ _ _ <<< "$entry"
    for sub in $subdirs; do
      [[ "$sub" == third_party/* ]] && continue
      local sub_rel="${sub}/CMakeLists.txt"
      if [[ -f "${root}/${sub_rel}" ]]; then
        _ingest_one "$sub_rel"
      fi
    done
  done
}

write_ingest_snapshot() {
  local out="${1:-$INGEST_SNAPSHOT}"
  mkdir -p "$(dirname "$out")"
  {
    echo '{'
    echo '  "version": 1,'
    echo "  \"root\": \"${INGEST_ROOT}\","
    echo '  "files": ['
    local first=1 rec rel list_dir incs subs names urls hashes
    for rec in "${INGEST_FILES[@]}"; do
      IFS='|' read -r rel list_dir incs subs names urls hashes <<< "$rec"
      [[ $first -eq 0 ]] && echo ','
      first=0
      echo -n "    {\"path\": \"${rel}\", \"list_dir\": \"${list_dir}\", \"includes_raw\": ["
      local sep="" tok
      for tok in $incs; do echo -n "${sep}\"${tok}\""; sep=", "; done
      echo -n "], \"subdirs_raw\": ["
      sep=""
      for tok in $subs; do echo -n "${sep}\"${tok}\""; sep=", "; done
      echo -n "], \"fetchcontent\": ["
      sep=""
      local i=0
      for name in $names; do
        local u="" h=""
        read -r -a _urls <<< "$urls"
        read -r -a _hashes <<< "$hashes"
        [[ ${#_urls[@]} -gt $i ]] && u="${_urls[$i]}"
        [[ ${#_hashes[@]} -gt $i ]] && h="${_hashes[$i]}"
        echo -n "${sep}{\"name\": \"${name}\", \"url\": \"${u}\", \"url_hash\": \"${h,,}\"}"
        sep=", "
        i=$((i + 1))
      done
      echo -n "]}"
    done
    echo
    echo '  ]'
    echo '}'
  } > "$out"
}
