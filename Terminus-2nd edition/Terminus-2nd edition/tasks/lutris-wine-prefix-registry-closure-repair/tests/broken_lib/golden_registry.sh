#!/usr/bin/env bash
# Merge duplicate slugs in parsed registry rows.

registry_merge_entries() {
  local parsed_file="$1"
  REGISTRY_WARNINGS=()
  REGISTRY_ERRORS=()
  : > "${REGISTRY_MERGED_FILE}"

  declare -A slug_runner=()
  declare -A slug_prefix=()
  declare -A slug_pin=()
  declare -A slug_requires_raw=()
  declare -A slug_provides_raw=()
  declare -A slug_seen=()

  while IFS='|' read -r kind a b c d; do
    case "$kind" in
      ENTRY)
        if [[ -n "${slug_seen[$a]:-}" ]]; then
          REGISTRY_WARNINGS+=("duplicate slug ${a} merged")
          local prev_runner="${slug_runner[$a]}"
          if [[ -n "$prev_runner" && -n "$b" && "$prev_runner" != "$b" ]]; then
            REGISTRY_ERRORS+=("conflicting runner for slug ${a}")
          fi
        else
          slug_seen["$a"]=1
          slug_runner["$a"]="$b"
          slug_prefix["$a"]="$c"
          slug_pin["$a"]="$d"
          slug_requires_raw["$a"]=""
          slug_provides_raw["$a"]=""
        fi
        ;;
      REQUIRES)
        slug_requires_raw["$a"]="${slug_requires_raw[$a]-} ${b}"
        ;;
      PROVIDES)
        local existing="${slug_provides_raw[$a]-}"
        if [[ -n "$existing" && "$existing" == *"${b}="* ]]; then
          local old_val
          old_val="$(echo "$existing" | tr ';' '\n' | grep "^${b}=" | head -1 | cut -d= -f2)"
          if [[ -n "$old_val" && "$old_val" != "$c" ]]; then
            REGISTRY_ERRORS+=("conflicting provides ${b} for slug ${a}")
          fi
        fi
        slug_provides_raw["$a"]="${slug_provides_raw[$a]-}${b}=${c};"
        ;;
    esac
  done < "${parsed_file}"

  if ((${#REGISTRY_ERRORS[@]} > 0)); then
    return 1
  fi

  local slug
  for slug in $(printf '%s\n' "${!slug_runner[@]}" | sort); do
    printf 'ENTRY|%s|%s|%s|%s\n' \
      "$slug" "${slug_runner[$slug]}" "${slug_prefix[$slug]}" "${slug_pin[$slug]}" \
      >> "${REGISTRY_MERGED_FILE}"
    local -a deps=()
    local dep
    for dep in ${slug_requires_raw[$slug]-}; do
      [[ -n "$dep" ]] && deps+=("$dep")
    done
    if ((${#deps[@]} > 0)); then
      mapfile -t deps < <(printf '%s\n' "${deps[@]}" | awk '!seen[$0]++' | sort)
      for dep in "${deps[@]}"; do
        printf 'REQUIRES|%s|%s\n' "$slug" "$dep" >> "${REGISTRY_MERGED_FILE}"
      done
    fi
    local prov="${slug_provides_raw[$slug]-}"
    if [[ -n "$prov" ]]; then
      declare -A merged_provides=()
      local item key val
      IFS=';' read -ra items <<< "${prov%;}"
      for item in "${items[@]}"; do
        [[ -z "$item" ]] && continue
        key="${item%%=*}"
        val="${item#*=}"
        merged_provides["$key"]="$val"
      done
      for key in $(printf '%s\n' "${!merged_provides[@]}" | sort); do
        printf 'PROVIDES|%s|%s|%s\n' "$slug" "$key" "${merged_provides[$key]}" \
          >> "${REGISTRY_MERGED_FILE}"
      done
    fi
  done
  return 0
}
