#!/usr/bin/env bash
# Ingest-time policy counter mode for phase_config.policy_mode.
# keep = export :CHAIN [pkts:bytes] exactly as parsed from the restore file.

lib_phase_b_policy() {
  local mode="keep"
  printf '%s\n' "${mode}"
}
