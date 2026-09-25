#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/common.sh"

normalize_dn() {
  local dn="$1" part attr val out="" IFS=','
  for part in $dn; do
    part="$(echo "$part" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$part" ]] && continue
    if [[ "$part" == *"="* ]]; then
      attr="${part%%=*}"
      val="${part#*=}"
      attr="$(echo "$attr" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      val="$(echo "$val" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      part="${attr}=${val}"
    fi
    if [[ -n "$out" ]]; then out="${out},${part}"; else out="$part"; fi
  done
  echo "$out"
}
