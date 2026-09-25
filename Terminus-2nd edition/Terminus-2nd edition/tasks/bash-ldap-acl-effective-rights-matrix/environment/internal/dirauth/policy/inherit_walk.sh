#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/dn/normalize.sh"

inherit_blocked_on_entry() {
  local entry="$1" ace_stream="$2"
  entry="$(normalize_dn "$entry")"
  local line target scope inherit
  while IFS= read -r line; do
    IFS='|' read -r src idx target scope inherit _ <<< "$line"
    target="$(normalize_dn "$target")"
    inherit="$(echo "$inherit" | tr '[:upper:]' '[:lower:]')"
    if [[ "$target" != "$entry" && "$inherit" =~ ^(yes|true|1)$ ]]; then
      return 0
    fi
  done <<< "$ace_stream"
  return 1
}
