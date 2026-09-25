#!/usr/bin/env bash
# Ingest-time table commit sequence for iptctl phase_config.commit_order.
# Export reads the frozen snapshot and must not re-invoke this helper.

lib_phase_a_sequence() {
  # Kernel commit order for mangle, nat, and filter (full sequence including
  # tables that may be absent from a given restore file).
  local tables=(mangle nat filter)
  local name
  for name in "${tables[@]}"; do
    printf '%s\n' "${name}"
  done
}
