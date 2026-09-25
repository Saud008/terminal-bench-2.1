#!/usr/bin/env bash
# Parse known_hosts lines into internal records.

kh__lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

kh__trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

kh__normalize_plain_token() {
  local token="$1"
  if [[ "$token" == \[*\]:* ]]; then
    local inner="${token#\[}"
    inner="${inner%%\]*}"
    local port="${token##*:}"
    printf '%s:%s' "$(kh__lower "$inner")" "$port"
  else
    kh__lower "$token"
  fi
}

kh__normalize_plain_hosts() {
  local hosts="$1"
  local -a raw=()
  local -a norm=()
  IFS=',' read -r -a raw <<< "$hosts"
  local tok
  for tok in "${raw[@]}"; do
    norm+=("$(kh__normalize_plain_token "$tok")")
  done
  local IFS=$'\n'
  local sorted
  sorted="$(printf '%s\n' "${norm[@]}" | LC_ALL=C sort)"
  local out=""
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    if [[ -n "$out" ]]; then
      out+=",$line"
    else
      out="$line"
    fi
  done <<< "$sorted"
  printf '%s' "$out"
}

kh__plain_port() {
  local hosts="$1"
  local first="${hosts%%,*}"
  if [[ "$first" == *:* ]]; then
    printf '%s' "${first##*:}"
  else
    printf '0'
  fi
}

kh__plain_sort_key() {
  local hosts="$1"
  local first="${hosts%%,*}"
  kh__lower "${first%%:*}"
}

kh_parse_line() {
  local line
  line="$(kh__trim "$1")"
  [[ -z "$line" || "$line" == \#* ]] && return 1

  local revoked=0
  local certauth=0
  if [[ "$line" == @revoked* ]]; then
    line="${line#@revoked}"
    line="$(kh__trim "$line")"
  fi
  if [[ "$line" == @cert-authority\ * ]]; then
    certauth=1
    line="${line#@cert-authority }"
  fi

  local host keytype keyblob comment=""
  read -r host keytype keyblob comment <<< "$line"
  [[ -z "$host" || -z "$keytype" || -z "$keyblob" ]] && return 1

  host="$(kh__lower "$host")"

  local kind plain_hosts="" salt="" hash="" port="0"
  if [[ "$host" == \|* ]]; then
    kind="hashed"
    salt="$(printf '%s' "$host" | awk -F'|' '{print $2}')"
    hash="$(printf '%s' "$host" | awk -F'|' '{print $3}')"
    plain_hosts=""
    port="0"
  else
    kind="plain"
    plain_hosts="$(kh__normalize_plain_hosts "$host")"
    salt=""
    hash=""
    port="$(kh__plain_port "$plain_hosts")"
  fi

  local sep=$'\x1f'
  printf '%s' \
    "${revoked}${sep}${certauth}${sep}${kind}${sep}${plain_hosts}${sep}${salt}${sep}${hash}${sep}${port}${sep}${keytype}${sep}${keyblob}${sep}${comment}"
}
