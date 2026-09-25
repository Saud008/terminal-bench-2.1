#!/usr/bin/env bash
# Correct export emission — oracle copies into /app/lib/kh_emit.sh.

kh_emit_record() {
  local rec="$1"
  local sep=$'\x1f'
  local IFS="$sep"
  read -r revoked certauth kind plain salt hash port keytype keyblob comment <<< "$rec"

  if [[ "${KH_INCLUDE_COMMENTS:-1}" == "0" ]]; then
    comment=""
  fi

  local marker=""
  if [[ "$revoked" == "1" ]]; then
    marker="@revoked"
  elif [[ "$certauth" == "1" ]]; then
    marker="@cert-authority"
  fi

  local host_field=""
  if [[ "$kind" == "hashed" ]]; then
    host_field="|1|${salt}|${hash}"
  else
    host_field="$plain"
  fi

  if [[ -n "$marker" ]]; then
    if [[ -n "$comment" ]]; then
      printf '%s %s %s %s %s\n' "$marker" "$host_field" "$keytype" "$keyblob" "$comment"
    else
      printf '%s %s %s %s\n' "$marker" "$host_field" "$keytype" "$keyblob"
    fi
  else
    if [[ -n "$comment" ]]; then
      printf '%s %s %s %s\n' "$host_field" "$keytype" "$keyblob" "$comment"
    else
      printf '%s %s %s\n' "$host_field" "$keytype" "$keyblob"
    fi
  fi
}

kh_emit_records() {
  local rec
  while IFS= read -r rec || [[ -n "$rec" ]]; do
    [[ -z "$rec" ]] && continue
    kh_emit_record "$rec"
  done
}
