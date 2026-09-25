#!/usr/bin/env bash
# Manifest and conf path helpers.

manifest_list_files() {
  local conf_dir="$1"
  local profile="${2:-default}"
  local manifest="${conf_dir}/manifest.txt"
  MANIFEST_FILES=()

  if [[ ! -f "${manifest}" ]]; then
    MANIFEST_ERROR="missing manifest: ${manifest}"
    return 1
  fi

  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    if [[ ! -f "${conf_dir}/${line}" ]]; then
      MANIFEST_ERROR="missing conf file: ${conf_dir}/${line}"
      return 1
    fi
    MANIFEST_FILES+=("$line")
  done < "${manifest}"

  if ((${#MANIFEST_FILES[@]} == 0)); then
    MANIFEST_ERROR="empty manifest for profile ${profile}"
    return 1
  fi
  MANIFEST_ERROR=""
  return 0
}
