#!/usr/bin/env bash
set -euo pipefail

key_suppressed() {
  local objects_json="$1" key="$2" holds_json="$3" window_end="$4"
  if echo "$objects_json" | jq -e --arg k "$key" '.[]|select(.key==$k and .legal_hold==true)' >/dev/null; then
    return 0
  fi
  if echo "$objects_json" | jq -e --arg k "$key" --arg we "${window_end}T23:59:59Z" \
    '.[]|select(.key==$k and (.retention_until!=null) and .retention_until > $we)' >/dev/null; then
    return 0
  fi
  local pfx
  while IFS= read -r pfx; do
    [[ -z "$pfx" ]] && continue
    [[ "$key" == "$pfx"* ]] && return 0
  done < <(echo "$holds_json" | jq -r '.legal_hold_prefixes[]?')
  return 1
}
