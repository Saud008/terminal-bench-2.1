#!/usr/bin/env bash
# Join continuation lines and parse mount commands.

conf_join_continuations() {
  local src="$1"
  local dst="$2"
  : > "${dst}"
  local line carry=""

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%"${line##*[![:space:]]}"}"
    if [[ "$line" =~ \\[[:space:]]*$ ]]; then
      local prefix="${line%\\}"
      prefix="${prefix%"${prefix##*[![:space:]]}"}"
      carry+="${prefix}"
      continue
    fi
    if [[ -n "$carry" ]]; then
      local trimmed="${line#"${line%%[![:space:]]*}"}"
      line="${carry}${trimmed}"
      carry=""
    fi
    printf '%s\n' "$line" >> "${dst}"
  done < "${src}"
  if [[ -n "$carry" ]]; then
    printf '%s\n' "$carry" >> "${dst}"
  fi
}

conf_parse_sections_to_rows() {
  local joined_file="$1"
  local source_file="$2"
  local out_file="$3"
  local current=""

  while IFS= read -r raw || [[ -n "$raw" ]]; do
    local line="${raw%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    if [[ "$line" == \[*\] ]]; then
      current="${line:1:${#line}-2}"
      current="${current,,}"
      continue
    fi
    [[ -z "$current" ]] && continue
    printf '%s|%s|%s\n' "$current" "$source_file" "$line" >> "${out_file}"
  done < "${joined_file}"
}

conf_parse_mount_tokens() {
  local cmd="$1"
  local op drive path
  read -r op drive path _rest <<< "$cmd"
  op="${op,,}"
  if [[ "$op" != "mount" && "$op" != "imgmount" ]]; then
    return 1
  fi
  drive="${drive%:}"
  drive="${drive^^}"
  CONF_PARSE_OP="$op"
  CONF_PARSE_DRIVE="$drive"
  CONF_PARSE_PATH="$path"
  return 0
}

conf_parse_remap_tokens() {
  local cmd="$1"
  local verb from to
  read -r verb from to _rest <<< "$cmd"
  verb="${verb,,}"
  if [[ "$verb" != "remap_drive" ]]; then
    return 1
  fi
  CONF_REMAP_FROM="${from%:}"
  CONF_REMAP_FROM="${CONF_REMAP_FROM^^}"
  CONF_REMAP_TO="${to%:}"
  CONF_REMAP_TO="${CONF_REMAP_TO^^}"
  return 0
}
