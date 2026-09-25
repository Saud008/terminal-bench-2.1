#!/usr/bin/env bash

PHASE_TRACE="/app/state/phase-trace.json"

trace_reset() {
  printf '{"steps":[]}\n' > "${PHASE_TRACE}"
}

trace_step() {
  local step="$1"
  if [ ! -f "${PHASE_TRACE}" ]; then
    trace_reset
  fi
  local tmp
  tmp="$(mktemp)"
  jq --arg s "${step}" '.steps += [$s]' "${PHASE_TRACE}" > "${tmp}"
  mv "${tmp}" "${PHASE_TRACE}"
}

load_manifest_field() {
  local tree="$1"
  local field="$2"
  jq -r ".${field}" "${tree}/manifest.json"
}

read_eapi() {
  local tree="$1"
  load_manifest_field "${tree}" eapi
}
