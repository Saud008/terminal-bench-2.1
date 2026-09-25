#!/usr/bin/env bash
# Packet stream reader via demux-read helper.

sd_read_packets() {
  local demo="$1"
  local packet_off="$2"
  local packet_len="$3"
  local out_ndjson="$4"
  /app/bin/demux-read "$demo" "$packet_off" "$packet_len" >"$out_ndjson"
}
