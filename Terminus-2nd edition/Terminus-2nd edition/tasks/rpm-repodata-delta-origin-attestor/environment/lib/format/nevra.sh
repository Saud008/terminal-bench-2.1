#!/usr/bin/env bash
# NEVRA formatting helpers shared by lineage staging.
nevra_without_epoch() {
  local name="$1"
  local ver="$2"
  local rel="$3"
  local arch="$4"
  printf '%s-%s-%s.%s' "$name" "$ver" "$rel" "$arch"
}
