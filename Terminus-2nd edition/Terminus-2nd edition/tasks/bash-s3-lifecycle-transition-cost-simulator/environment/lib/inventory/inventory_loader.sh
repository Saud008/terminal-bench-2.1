#!/usr/bin/env bash
set -euo pipefail
S3LC_LIB="${S3LC_LIB:-/app/lib}"
source "${S3LC_LIB}/common.sh"

load_inventory_jsonl() {
  local path="$1" bucket="$2"
  local -a objs=()
  local line key vid size_sum=0
  declare -A seen=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    key="$(echo "$line" | jq -r '.key')"
    vid="$(echo "$line" | jq -r '.version_id')"
    seen["${key}|${vid}"]="$line"
    size_sum=$((size_sum + $(echo "$line" | jq -r '.size_bytes')))
  done < "$path"
  local k
  for k in "${!seen[@]}"; do
    objs+=("${seen[$k]}")
  done
  local joined=""
  local i
  for ((i=0; i<${#objs[@]}; i++)); do
    joined+="${objs[$i]}"
    [[ $i -lt $((${#objs[@]} - 1)) ]] && joined+=$'\n'
  done
  local fp
  fp="$(sha256_hex "$joined")"
  jq -n --arg bucket "$bucket" --arg fp "$fp" --argjson rows "$(printf '%s\n' "${objs[@]}" | jq -s -c '.')" \
    '{schema_version:1, bucket:$bucket, inventory_fingerprint:$fp, objects:$rows, simulation:null}'
}
