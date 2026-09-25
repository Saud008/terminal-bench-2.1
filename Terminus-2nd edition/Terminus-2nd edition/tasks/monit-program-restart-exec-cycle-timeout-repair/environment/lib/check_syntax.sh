#!/usr/bin/env bash

# Monit check program syntax line helper.
monit_parse_check_line() {
  local line="$1"
  if [[ "${line}" == check\ program* ]]; then
    echo ok
  else
    echo skip
  fi
}
