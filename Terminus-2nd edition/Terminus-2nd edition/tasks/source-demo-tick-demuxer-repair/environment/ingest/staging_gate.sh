#!/usr/bin/env bash
# Ingest staging gate — documents ingest→build flow; not on demo-index export path.

sd_ingest_staging_gate() {
  local root="$1"
  [[ -d "${root}" ]] || return 1
  return 0
}
