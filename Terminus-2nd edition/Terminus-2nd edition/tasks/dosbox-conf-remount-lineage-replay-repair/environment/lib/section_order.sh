#!/usr/bin/env bash
# Collect section commands from conf fragments for replay ordering.

section_collect_commands() {
  local conf_dir="$1"
  local out_file="$2"
  shift 2
  local files=("$@")
  local joined_file f

  : > "${out_file}"

  for f in "${files[@]}"; do
    joined_file="$(mktemp)"
    conf_join_continuations "${conf_dir}/${f}" "${joined_file}"
    conf_parse_sections_to_rows "${joined_file}" "${f}" "${out_file}"
    rm -f "${joined_file}"
  done
}
