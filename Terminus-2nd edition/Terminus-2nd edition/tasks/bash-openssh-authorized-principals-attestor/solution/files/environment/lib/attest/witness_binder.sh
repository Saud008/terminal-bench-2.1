#!/usr/bin/env bash
set -euo pipefail

SSHAP_LIB="${SSHAP_LIB:-/app/lib}"
source "${SSHAP_LIB}/common.sh"
source "${SSHAP_LIB}/sshdmatch/scope_resolver.sh"
source "${SSHAP_LIB}/certgate/wildcard_policy.sh"

_row_matches() {
  fnmatch_case "$1" "$2"
}

_decide_probe() {
  local ledger="$1" match_dir="$2" probe_json="$3"
  local pid user host principal fp signed ca_id scope
  pid="$(echo "$probe_json" | jq -r '.probe_id')"
  user="$(echo "$probe_json" | jq -r '.user')"
  host="$(echo "$probe_json" | jq -r '.host')"
  principal="$(echo "$probe_json" | jq -r '.principal')"
  fp="$(echo "$probe_json" | jq -r '.key_fingerprint' | tr '[:upper:]' '[:lower:]')"
  signed="$(echo "$probe_json" | jq -r '.signed_by_ca')"
  ca_id="$(echo "$probe_json" | jq -r '.ca_id // ""')"
  scope="$(resolve_match_scope "$match_dir" "$user" "$host")"

  if jq -e --arg fp "$fp" '.revoked[]? | select(. == $fp)' "$ledger" >/dev/null; then
    local ad
    ad="$(sha256_hex "${pid}|deny|revoked||${scope}")"
    jq -n --arg pid "$pid" --arg s "$scope" --arg ad "$ad" '{probe_id:$pid, verdict:"deny", reason:"revoked", winning_principal:"", scope_id:$s, binding_seal:$ad}'
    return 0
  fi
  if ! enforce_wildcard_policy "$principal"; then
    local ad
    ad="$(sha256_hex "${pid}|deny|wildcard_denied||${scope}")"
    jq -n --arg pid "$pid" --arg s "$scope" --arg ad "$ad" '{probe_id:$pid, verdict:"deny", reason:"wildcard_denied", winning_principal:"", scope_id:$s, binding_seal:$ad}'
    return 0
  fi
  if [[ "$signed" == "true" && -n "$ca_id" ]]; then
    local ok=0 a
    while IFS= read -r a; do
      [[ -z "$a" ]] && continue
      [[ "$a" == "*" || "$a" == "$principal" ]] && ok=1
    done < <(jq -r --arg id "$ca_id" '.cas[]? | select(.ca_id==$id) | .principals_allowed[]' "$ledger")
    if [[ "$ok" -eq 0 ]]; then
      local ad
      ad="$(sha256_hex "${pid}|deny|ca_scope||${scope}")"
      jq -n --arg pid "$pid" --arg s "$scope" --arg ad "$ad" '{probe_id:$pid, verdict:"deny", reason:"ca_scope", winning_principal:"", scope_id:$s, binding_seal:$ad}'
      return 0
    fi
  fi

  local best="" best_deny=1 best_rank=999999
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    local p_scope deny rank text dnum
    p_scope="$(echo "$row" | jq -r '.scope_id')"
    deny="$(echo "$row" | jq -r '.deny')"
    rank="$(echo "$row" | jq -r '.rank')"
    text="$(echo "$row" | jq -r '.principal')"
    if [[ "$scope" == "global" ]]; then
      [[ "$p_scope" != "global" ]] && continue
    else
      [[ "$p_scope" != "$scope" ]] && continue
    fi
    _row_matches "$text" "$principal" || continue
    dnum=0
    [[ "$deny" == "true" || "$deny" == "1" ]] && dnum=0 || dnum=1
    if [[ "$dnum" -lt "$best_deny" || ( "$dnum" -eq "$best_deny" && "$rank" -lt "$best_rank" ) ]]; then
      best_deny="$dnum"
      best_rank="$rank"
      best="$text"
      if [[ "$dnum" -eq 0 ]]; then
        local ad
        ad="$(sha256_hex "${pid}|deny|principal_match|${text}|${scope}")"
        jq -n --arg pid "$pid" --arg w "$text" --arg s "$scope" --arg ad "$ad" '{probe_id:$pid, verdict:"deny", reason:"principal_match", winning_principal:$w, scope_id:$s, binding_seal:$ad}'
        return 0
      fi
    fi
  done < <(jq -c '.principals[]' "$ledger")

  if [[ -n "$best" ]]; then
    local ad
    ad="$(sha256_hex "${pid}|allow|principal_match|${best}|${scope}")"
    jq -n --arg pid "$pid" --arg w "$best" --arg s "$scope" --arg ad "$ad" '{probe_id:$pid, verdict:"allow", reason:"principal_match", winning_principal:$w, scope_id:$s, binding_seal:$ad}'
    return 0
  fi
  local ad
  ad="$(sha256_hex "${pid}|deny|no_match||${scope}")"
  jq -n --arg pid "$pid" --arg s "$scope" --arg ad "$ad" '{probe_id:$pid, verdict:"deny", reason:"no_match", winning_principal:"", scope_id:$s, binding_seal:$ad}'
}

emit_principals_attestation() {
  local ledger="$1" match_dir="$2" probes="$3" out="$4"
  ensure_runtime_dirs
  local probe_doc ids seal_lines="" session_bindings=()
  probe_doc="$(cat "$probes")"
  mapfile -t ids < <(echo "$probe_doc" | jq -r '.probes[].probe_id' | LC_ALL=C sort)
  local pid dec
  for pid in "${ids[@]}"; do
    local pjson
    pjson="$(echo "$probe_doc" | jq -c --arg id "$pid" '.probes[] | select(.probe_id==$id)')"
    dec="$(_decide_probe "$ledger" "$match_dir" "$pjson")"
    session_bindings+=("$dec")
    seal_lines+="$(echo "$dec" | jq -r '.binding_seal')"$'\n'
  done
  local bundle_seal
  bundle_seal="$(sha256_hex "$seal_lines")"
  local bind_json
  bind_json="$(printf '%s\n' "${session_bindings[@]}" | jq -s '.')"
  jq -n --argjson dec "$bind_json" --arg rd "$bundle_seal" '{schema_version:1, session_bindings:$dec, bundle_seal:$rd}' > "$out"
  echo "SSHAP:ATTEST_OK"
}
