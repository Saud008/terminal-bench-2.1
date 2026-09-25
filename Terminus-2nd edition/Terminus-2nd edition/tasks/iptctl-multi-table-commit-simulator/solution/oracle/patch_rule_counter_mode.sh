#!/usr/bin/env bash
# Ingest-time per-rule counter mode for phase_config.rule_counter_mode.
# keep = export -A trailing [pkts:bytes]; missing suffix remains 0.

lib_phase_c_rules() {
  local mode="keep"
  printf '%s\n' "${mode}"
}
