#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

netifd_metric_cache_write() {
  local scenario_json="$1" iface="$2"
  local config_metric
  config_metric="$(netifd_scenario_field "$scenario_json" config_metric)"
  mkdir -p "${NETIFD_STATE_DIR}"
  echo "${iface}:${config_metric}" > "${NETIFD_STATE_DIR}/metric.cache"
}
