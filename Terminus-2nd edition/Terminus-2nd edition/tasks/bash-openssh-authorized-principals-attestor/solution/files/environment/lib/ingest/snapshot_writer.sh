#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"
source "${SSHAP_LIB}/sshcert/parse_lines.sh"
source "${SSHAP_LIB}/sshcert/rank_winners.sh"
source "${SSHAP_LIB}/truststore/ca_reader.sh"
source "${SSHAP_LIB}/revocation/krl_reader.sh"

_compute_ledger_fingerprint() {
  local ranked="$1" ca_lines="$2" rev_lines="$3"
  local lines=() row
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    IFS='|' read -r scope deny rank principal <<< "$row"
    lines+=("${scope};${deny};${rank};${principal}")
  done < <(echo "$ranked")
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    IFS='|' read -r ca_id _ allowed _ <<< "$row"
    lines+=("${ca_id};${allowed}")
  done < <(echo "$ca_lines" | LC_ALL=C sort)
  while IFS= read -r fp; do
    [[ -z "$fp" ]] && continue
    lines+=("revoked;${fp}")
  done < <(echo "$rev_lines" | LC_ALL=C sort)
  local joined=""
  local i
  for ((i=0; i<${#lines[@]}; i++)); do
    joined+="${lines[$i]}"
    [[ "$i" -lt $((${#lines[@]} - 1)) ]] && joined+=$'\n'
  done
  sha256_hex "$joined"
}

write_trust_ledger() {
  local principals_dir="$1" ca_dir="$2" krl="$3" out="$4"
  ensure_runtime_dirs
  local raw ranked princ_json cas_json rev_json digest old_digest seq
  raw="$(read_principal_files "$principals_dir")"
  ranked="$(order_principal_rows "$raw")"
  princ_json="[]"
  [[ -n "$ranked" ]] && princ_json="$(echo "$ranked" | jq -R -s -c 'split("\n")|map(select(length>0))|map(split("|"))|map({scope_id:.[0], deny:(.[1]=="1"), rank:(.[2]|tonumber), principal:.[3]})')"
  local ca_lines
  ca_lines="$(read_ca_material "$ca_dir" || true)"
  cas_json="[]"
  [[ -n "$ca_lines" ]] && cas_json="$(echo "$ca_lines" | jq -R -s -c 'split("\n")|map(select(length>0))|map(split("|"))|map({ca_id:.[0], key_type:.[1], principals_allowed:(if .[2]=="*" then ["*"] else (.[2]|split(",")) end), fingerprint:.[3]})')"
  local rev_lines
  rev_lines="$(read_krl_revocations "$krl" || true)"
  rev_json="[]"
  [[ -n "$rev_lines" ]] && rev_json="$(echo "$rev_lines" | jq -R -s -c 'split("\n")|map(select(length>0))')"
  digest="$(_compute_ledger_fingerprint "$ranked" "$ca_lines" "$rev_lines")"
  old_digest=""
  [[ -f "$out" ]] && old_digest="$(jq -r '.ledger_fingerprint // empty' "$out" 2>/dev/null || true)"
  seq="$(read_scan_generation)"
  if [[ "$digest" != "$old_digest" ]]; then
    seq=$((seq + 1))
    write_scan_generation "$seq"
  fi
  jq -n --argjson principals "$princ_json" --argjson cas "$cas_json" --argjson revoked "$rev_json" --arg digest "$digest" \
    '{schema_version:1, principals:$principals, cas:$cas, revoked:$revoked, ledger_fingerprint:$digest}' > "$out"
  echo "SSHAP:SCAN_OK"
}
