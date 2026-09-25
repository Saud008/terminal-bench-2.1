#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_write_export() {
  local export_path="$1"
  local payload="$2"
  roam_write_json_file "${export_path}" "${payload}"
}
