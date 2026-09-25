#!/usr/bin/env bash
# Sensor type name resolution from TSV and docs.
set -euo pipefail

SENSOR_TSV="${APP_ROOT:-/app}/config/sensor-types.tsv"
DOC_EXTRA="${APP_ROOT:-/app}/docs/ipmi-sel.md"

sensor_lookup_key() {
  local sensor_type="$1"
  printf '0x%02X' "${sensor_type}"
}

sensor_name_for() {
  local sensor_type="$1"
  local key name
  key="$(sensor_lookup_key "${sensor_type}")"
  name="$(awk -F '\t' -v k="${key}" '$1 == k {print $2; exit}' "${SENSOR_TSV}" 2>/dev/null || true)"
  if [ -n "${name}" ]; then
    echo "${name}"
    return 0
  fi
  name="$(awk -v hx="${key}" '
    $0 ~ "^\\| " hx " \\|" {
      gsub(/^\| /, "", $0)
      gsub(/ \|$/, "", $0)
      split($0, parts, "|")
      gsub(/^ +| +$/, "", parts[2])
      print parts[2]
      exit
    }
  ' "${DOC_EXTRA}" 2>/dev/null || true)"
  [ -n "${name}" ] || name="unknown"
  echo "${name}"
}
