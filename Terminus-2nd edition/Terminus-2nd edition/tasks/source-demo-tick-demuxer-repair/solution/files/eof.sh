#!/usr/bin/env bash
# EOF / truncation probe for a single demo file.

sd_probe_truncation() {
  local demo="$1"
  read -r _ _ _ _ plen _ _ poff < <(sd_read_header "$demo")
  local tmp
  tmp="$(mktemp)"
  local rc=0
  /app/bin/demux-read "$demo" "$poff" "$plen" >"$tmp" || rc=$?
  rm -f "$tmp"
  exit "$rc"
}
