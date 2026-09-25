#!/usr/bin/env bash
# Nested-block ORGMAIL fallback helper.
fork_orgmail_fallback() {
  local msg_id="$1"
  local rid="$2"
  local delivered="$3"
  if [[ "$delivered" == "1" ]]; then
    return 0
  fi
  if [[ -z "$ENV_ORGMAIL" ]]; then
    return 0
  fi
  deliver_record "$msg_id" "$ENV_ORGMAIL" "$rid" "orgmail_fork_fallback"
}
