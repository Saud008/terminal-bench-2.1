#!/usr/bin/env bash
# Legacy export wrapper — not used by demo-index build hot path.

sd_legacy_wrap_export() {
  echo "legacy export path disabled" >&2
  return 1
}
