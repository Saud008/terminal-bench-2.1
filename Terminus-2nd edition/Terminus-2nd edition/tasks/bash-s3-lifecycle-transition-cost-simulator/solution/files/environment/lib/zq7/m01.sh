#!/usr/bin/env bash
set -euo pipefail

tag_prefixes_match() {
  local tags_json="$1" prefixes_json="$2"
  local count
  count="$(echo "$prefixes_json" | jq 'length')"
  [[ "$count" -eq 0 ]] && return 0
  local ok=0
  local key val prefix
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    prefix="$(echo "$prefixes_json" | jq -r --arg k "$key" '.[$k] // empty')"
    [[ -z "$prefix" || "$prefix" == "null" ]] && return 1
    val="$(echo "$tags_json" | jq -r --arg k "$key" '.[$k] // empty')"
    [[ "$val" == "$prefix"* ]] || return 1
    ok=$((ok + 1))
  done < <(echo "$prefixes_json" | jq -r 'keys[]')
  [[ "$ok" -ge "$count" ]]
}
