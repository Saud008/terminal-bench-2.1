#!/usr/bin/env bash
# Packet stream reader via demux-read helper.

sd_read_packets() {
  local demo="$1"
  local packet_off="$2"
  local packet_len="$3"
  local out_ndjson="$4"
  local rc=0
  /app/bin/demux-read "$demo" "$packet_off" "$packet_len" >"$out_ndjson" || rc=$?
  if [[ $rc -eq 2 ]]; then
    return 0
  fi
  return "$rc"
}
