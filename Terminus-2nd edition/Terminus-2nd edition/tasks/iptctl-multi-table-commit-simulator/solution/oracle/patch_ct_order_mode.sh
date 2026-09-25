#!/usr/bin/env bash
# Ingest-time conntrack ordering mode for phase_config.ct_mode.
# chain = preserve commit-walk collection order (not lexical sort of spec).

lib_phase_e_ct() {
  local mode="chain"
  printf '%s\n' "${mode}"
}
