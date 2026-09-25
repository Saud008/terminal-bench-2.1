#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

monit_record_transition() {
  local idfile="$1"
  local transition="$2"
  local t="$3"
  mkdir -p "$(dirname "${idfile}")"
  printf 'state=%s t=%s\n' "${transition}" "${t}" > "${idfile}"
  echo idfile_first > "${idfile}.order"
  printf '%s notify t=%s\n' "${transition}" "${t}" >> "${MONIT_NOTIFY_LOG}"
}
