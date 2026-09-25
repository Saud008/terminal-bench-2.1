#!/usr/bin/env bash
# Transitive requires closure and runner resolution.

closure_build() {
  local merged_file="$1"
  local root_slug="$2"
  CLOSURE_ORDER=()
  CLOSURE_CYCLES=()
  CLOSURE_ERRORS=()
  CLOSURE_EDGE_COUNT=0
  CLOSURE_MAX_DEPTH=0
  CLOSURE_RUNNER=""
  CLOSURE_DXVK_VERSION=""

  declare -A slug_runner=()
  declare -A slug_pin=()
  declare -A slug_requires=()
  declare -A slug_provides=()

  while IFS='|' read -r kind a b c d; do
    case "$kind" in
      ENTRY)
        slug_runner["$a"]="$b"
        slug_pin["$a"]="$d"
        slug_requires["$a"]=""
        ;;
      REQUIRES)
        slug_requires["$a"]="${slug_requires[$a]-} $b"
        CLOSURE_EDGE_COUNT=$((CLOSURE_EDGE_COUNT + 1))
        ;;
      PROVIDES)
        if [[ "$b" == "dxvk_version" ]]; then
          slug_provides["$a"]="$c"
        fi
        ;;
    esac
  done < "${merged_file}"

  if [[ -z "${slug_runner[$root_slug]:-}" ]]; then
    CLOSURE_RUNNER=""
  else
    CLOSURE_RUNNER="${slug_runner[$root_slug]}"
  fi

  CLOSURE_ORDER=("$root_slug")
  for dep in ${slug_requires[$root_slug]-}; do
    [[ -n "$dep" ]] && CLOSURE_ORDER+=("$dep")
  done

  if [[ -n "${slug_pin[$root_slug]:-}" && -n "${slug_provides[$root_slug]:-}" ]]; then
    CLOSURE_DXVK_VERSION="${slug_provides[$root_slug]}"
  fi

  CLOSURE_MAX_DEPTH=1
}
