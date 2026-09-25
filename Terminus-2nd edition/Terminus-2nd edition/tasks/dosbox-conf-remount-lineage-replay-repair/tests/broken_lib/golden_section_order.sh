#!/usr/bin/env bash
# Collect config before autoexec across manifest files.

section_collect_commands() {
  local conf_dir="$1"
  local out_file="$2"
  shift 2
  local files=("$@")
  local raw_file joined_file f

  raw_file="$(mktemp)"
  joined_file="$(mktemp)"
  : > "${out_file}"
  : > "${raw_file}"

  for f in "${files[@]}"; do
    conf_join_continuations "${conf_dir}/${f}" "${joined_file}"
    conf_parse_sections_to_rows "${joined_file}" "${f}" "${raw_file}"
  done

  rm -f "${joined_file}"

  while IFS='|' read -r sec src cmd; do
    [[ "$sec" == "config" ]] && printf '%s|%s|%s\n' "$sec" "$src" "$cmd" >> "${out_file}"
  done < "${raw_file}"

  while IFS='|' read -r sec src cmd; do
    [[ "$sec" == "autoexec" ]] && printf '%s|%s|%s\n' "$sec" "$src" "$cmd" >> "${out_file}"
  done < "${raw_file}"

  rm -f "${raw_file}"
}
