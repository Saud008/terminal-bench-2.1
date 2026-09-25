#!/usr/bin/env bash
set -euo pipefail

attr_rule_matches() {
  local ace_attrs="$1" requested="$2"
  local a
  IFS=',' read -ra arr <<< "$ace_attrs"
  for a in "${arr[@]}"; do
    a="$(echo "$a" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ "$a" == "*" ]] && return 0
    [[ "$(echo "$a" | tr '[:upper:]' '[:lower:]')" == "$(echo "$requested" | tr '[:upper:]' '[:lower:]')" ]] && return 0
  done
  return 1
}
