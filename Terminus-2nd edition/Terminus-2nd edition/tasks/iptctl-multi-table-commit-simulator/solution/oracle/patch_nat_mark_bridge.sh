#!/usr/bin/env bash
# Ingest-time mangle→NAT mark bridge mode for phase_config.mark_mode.
# linked = NAT -m mark rules activate only after mangle --set-mark commits.

lib_phase_d_mark() {
  local mode="linked"
  printf '%s\n' "${mode}"
}
