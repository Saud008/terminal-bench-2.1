#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"

read_ca_material() {
  local dir="$1"
  local f line
  for f in "$dir"/*.pub; do
    [[ -f "$f" ]] || continue
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ "$line" =~ ^# ]] && continue
      [[ -z "${line// }" ]] && continue
      local allowed="*" ca_id key_type blob
      if [[ "$line" =~ ^cert-authority ]]; then
        if [[ "$line" =~ principals=\"([^\"]+)\" ]]; then
          allowed="$(echo "${BASH_REMATCH[1]}" | tr "," " ")"
        fi
        key_type="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^ssh-/) {print $i; exit}}')"
        blob="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^ssh-/) {print $(i+1); exit}}')"
        ca_id="$(echo "$line" | awk '{print $NF}')"
      else
        key_type="$(echo "$line" | awk '{print $1}')"
        blob="$(echo "$line" | awk '{print $2}')"
        ca_id="$(echo "$line" | awk '{print $3}')"
      fi
      echo "${ca_id}|${key_type}|${allowed}|${blob}"
    done < "$f"
  done
}
