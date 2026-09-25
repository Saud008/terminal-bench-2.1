#!/usr/bin/env bash
# Decoy module not on the scan, compile, or publish path.
slot_name_lex_helper() {
  local devices="$1"
  echo "$devices" | tr ',' '\n' | sort | paste -sd,
}
