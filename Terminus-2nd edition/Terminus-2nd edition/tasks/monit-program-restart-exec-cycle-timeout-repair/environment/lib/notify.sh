#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Transition notify + monit id state file updates.
monit_record_transition() {
  local idfile="$1"
  local transition="$2"
  local t="$3"
  mkdir -p "$(dirname "${idfile}")"
  echo notify_first > "${idfile}.order"
  printf '%s notify t=%s\n' "${transition}" "${t}" >> "${MONIT_NOTIFY_LOG}"
  printf 'state=%s t=%s\n' "${transition}" "${t}" > "${idfile}"
}
