#!/bin/bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/resolve/dep_closure.sh"
source "${APP_ROOT}/lib/resolve/conflict_resolve.sh"
source "${APP_ROOT}/lib/resolve/family_swap.sh"
source "${APP_ROOT}/lib/resolve/path_order.sh"
source "${APP_ROOT}/lib/resolve/staging_write.sh"

snapshot=""
request=""
staging=""
run_id="default"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --snapshot) snapshot="$2"; shift 2 ;;
    --request) request="$2"; shift 2 ;;
    --staging) staging="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "${snapshot}" && -n "${request}" && -n "${staging}" ]] || {
  echo "need --snapshot --request --staging" >&2
  exit 2
}

declare -a records=()
load_snapshot_records "${snapshot}" records

declare -a requested=()
while IFS= read -r line || [[ -n "${line}" ]]; do
  line="${line%%#*}"
  line="$(echo "${line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "${line}" ]] && continue
  [[ "${line}" == load\ * ]] && requested+=("${line#load }")
done < "${request}"

declare -a closure_order=()
closure_load_order requested records closure_order

declare -a after_conflict=() conflict_unloads=()
apply_conflicts closure_order records after_conflict conflict_unloads

declare -a family_unloads=()
apply_family_swaps after_conflict records family_unloads

declare -a all_unloads=("${family_unloads[@]}" "${conflict_unloads[@]}")

declare -a mutations=()
build_path_mutations after_conflict records mutations

declare -a path_final=()
apply_path_stack mutations path_final

export STAGING_UNLOADS=("${all_unloads[@]}")
export STAGING_LOADS=("${after_conflict[@]}")
export STAGING_MUTATIONS=("${mutations[@]}")
export STAGING_PATH_FINAL=("${path_final[@]}")

req_hash="$(request_file_hash "${request}")"
cat_digest="$(read_catalog_digest "${snapshot}")"
staging_write "${staging}" "${run_id}" "${req_hash}" "${cat_digest}"
