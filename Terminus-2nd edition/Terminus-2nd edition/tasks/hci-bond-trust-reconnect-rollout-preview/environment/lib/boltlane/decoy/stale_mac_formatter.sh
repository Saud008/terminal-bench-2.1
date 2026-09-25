#!/usr/bin/env bash
# Unused module — not reached by fleet_intake, eligibility_engine, or atlas_emit.
stale_mac_formatter() {
  local macs="$1"
  echo "$macs" | tr ',' '\n' | sort | paste -sd,
}
