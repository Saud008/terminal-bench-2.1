#!/usr/bin/env bash
# Graph loading helpers for lt-canonicalize.

lt_graph_load() {
  local root="$1"
  local work="$2"
  mkdir -p "${work}"
  LT_ROOT="${root}"
  LT_WORK="${work}"
  LT_IDS=()
  mapfile -t LT_LA_PATHS < <(find "${root}" -type f -name '*.la' | LC_ALL=C sort)
  if [ "${#LT_LA_PATHS[@]}" -eq 0 ]; then
    return 2
  fi
  for la in "${LT_LA_PATHS[@]}"; do
    local id
    id="$(basename "${la}" .la)"
    LT_IDS+=("${id}")
    /usr/local/bin/ltparse "${la}" > "${work}/${id}.fields"
  done
  LT_IDS=($(printf '%s\n' "${LT_IDS[@]}" | LC_ALL=C sort -u))
}

lt_field() {
  local id="$1"
  local key="$2"
  local file="${LT_WORK}/${id}.fields"
  grep -m1 "^${key}=" "${file}" 2>/dev/null | cut -d= -f2- || true
}

lt_direct_deps() {
  local id="$1"
  local deps_raw
  deps_raw="$(lt_field "${id}" dependency_libs)"
  local out=()
  local tok
  for tok in ${deps_raw}; do
    if [[ "${tok}" == -l* ]]; then
      out+=("${tok#-l}")
    fi
  done
  printf '%s\n' "${out[@]}"
}

lt_all_nodes() {
  printf '%s\n' "${LT_IDS[@]}"
}
