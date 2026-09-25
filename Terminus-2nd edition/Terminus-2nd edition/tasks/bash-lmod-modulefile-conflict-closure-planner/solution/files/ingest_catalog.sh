#!/bin/bash
# Parse line-oriented module catalog files into normalized records.
set -euo pipefail

parse_catalog_dir() {
  local dir="$1"
  local -n _out="$2"
  _out=()
  local f rec
  shopt -s nullglob
  for f in "${dir}"/*.mod "${dir}"/*.module; do
    rec="$(parse_catalog_file "${f}")"
    _out+=("${rec}")
  done
  shopt -u nullglob
}

parse_catalog_file() {
  local file="$1"
  local mod="" family="" priority="0"
  local -a deps=() conflicts=() prepends=() appends=()
  local line key val
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%%#*}"
    line="$(echo "${line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "${line}" ]] && continue
    key="${line%% *}"
    val="${line#* }"
    case "${key}" in
      @module) mod="${val}" ;;
      @family) family="${val}" ;;
      @priority) priority="${val}" ;;
      @depends|@requires) deps+=("${val}") ;;
      @conflict) conflicts+=("${val}") ;;
      @prepend) prepends+=("${val}") ;;
      @append) appends+=("${val}") ;;
    esac
  done < "${file}"
  if [[ -z "${mod}" ]]; then
    echo "missing @module in ${file}" >&2
    return 1
  fi
  local dep_csv conflict_csv pre_csv app_csv
  dep_csv=$(IFS=,; echo "${deps[*]}")
  conflict_csv=$(IFS=,; echo "${conflicts[*]}")
  pre_csv=$(IFS='|'; echo "${prepends[*]}")
  app_csv=$(IFS='|'; echo "${appends[*]}")
  printf 'module|%s|family=%s|priority=%s|depends=%s|conflicts=%s|prepends=%s|appends=%s' \
    "${mod}" "${family}" "${priority}" "${dep_csv}" "${conflict_csv}" "${pre_csv}" "${app_csv}"
}

catalog_digest_from_records() {
  local -n _recs="$1"
  local joined
  if ((${#_recs[@]} == 0)); then
    joined=""
  else
    mapfile -t _sorted < <(printf '%s\n' "${_recs[@]}" | LC_ALL=C sort)
    local IFS=$'\n'
    joined="${_sorted[*]}"
  fi
  printf '%s' "${joined}" | sha256sum | awk '{print $1}'
}

write_catalog_snapshot() {
  local out="$1"
  shift
  local -a recs=("$@")
  local -a sorted_recs=()
  mapfile -t sorted_recs < <(printf '%s\n' "${recs[@]}" | LC_ALL=C sort)
  local digest
  digest="$(catalog_digest_from_records sorted_recs)"
  {
    echo "schema_version=1"
    echo "catalog_digest=${digest}"
    printf '%s\n' "${sorted_recs[@]}"
  } > "${out}"
}
