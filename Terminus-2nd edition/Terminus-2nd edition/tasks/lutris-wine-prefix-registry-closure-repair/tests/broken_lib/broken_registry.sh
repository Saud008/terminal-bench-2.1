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
  declare -A slug_requires=()
  declare -A slug_provides=()

  while IFS='|' read -r kind a b c d; do
    case "$kind" in
      ENTRY)
        slug_runner["$a"]="$b"
        slug_prefix["$a"]="$c"
        slug_pin["$a"]="$d"
        slug_requires["$a"]=""
        slug_provides["$a"]=""
        ;;
      REQUIRES)
        slug_requires["$a"]="${slug_requires[$a]-} $b"
        ;;
      PROVIDES)
        slug_provides["$a"]="${slug_provides[$a]-}${b}=${c};"
        ;;
    esac
  done < "${parsed_file}"

  for slug in "${!slug_runner[@]}"; do
    printf 'ENTRY|%s|%s|%s|%s\n' \
      "$slug" "${slug_runner[$slug]}" "${slug_prefix[$slug]}" "${slug_pin[$slug]}" \
      >> "${REGISTRY_MERGED_FILE}"
    for dep in ${slug_requires[$slug]-}; do
      [[ -n "$dep" ]] && printf 'REQUIRES|%s|%s\n' "$slug" "$dep" >> "${REGISTRY_MERGED_FILE}"
    done
    local prov="${slug_provides[$slug]-}"
    if [[ -n "$prov" ]]; then
      local item key val
      IFS=';' read -ra items <<< "${prov%;}"
      for item in "${items[@]}"; do
        [[ -z "$item" ]] && continue
        key="${item%%=*}"
        val="${item#*=}"
        printf 'PROVIDES|%s|%s|%s\n' "$slug" "$key" "$val" >> "${REGISTRY_MERGED_FILE}"
      done
    fi
  done
}
