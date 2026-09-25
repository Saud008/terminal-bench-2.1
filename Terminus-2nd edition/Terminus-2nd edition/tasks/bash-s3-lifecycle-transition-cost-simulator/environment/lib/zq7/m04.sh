#!/usr/bin/env bash
set -euo pipefail

key_suppressed() {
  local objects_json="$1" key="$2" holds_json="$3" window_end="$4"
  local cur
  cur="$(echo "$objects_json" | jq -c --arg k "$key" 'map(select(.key==$k and .current_version))|.[0]')"
  [[ "$(echo "$cur" | jq -r '.legal_hold')" == "true" ]] && return 0
  local until
  until="$(echo "$cur" | jq -r '.retention_until // empty')"
  if [[ -n "$until" && "$until" > "${window_end}T23:59:59Z" ]]; then
    return 0
  fi
  local pfx
  while IFS= read -r pfx; do
    [[ -z "$pfx" ]] && continue
    [[ "$key" == "$pfx"* ]] && return 0
  done < <(echo "$holds_json" | jq -r '.legal_hold_prefixes[]?')
  return 1
}
