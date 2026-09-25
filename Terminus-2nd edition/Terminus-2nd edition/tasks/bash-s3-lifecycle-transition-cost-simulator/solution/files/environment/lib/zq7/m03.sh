#!/usr/bin/env bash
set -euo pipefail

apply_transitions() {
  local age="$1" rule_json="$2" storage_class="$3"
  local cls="$storage_class"
  local row days target
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    days="$(echo "$row" | jq -r '.days')"
    target="$(echo "$row" | jq -r '.storage_class')"
    if [[ "$age" -ge "$days" ]]; then
      cls="$target"
    fi
  done < <(echo "$rule_json" | jq -c '.transitions | sort_by(.days)[]')
  echo "$cls"
}

should_expire() {
  local age="$1" rule_json="$2"
  local ed
  ed="$(echo "$rule_json" | jq -r '.expiration.days // empty')"
  [[ -n "$ed" && "$age" -ge "$ed" ]]
}

should_expire_noncurrent() {
  local age="$1" rule_json="$2"
  local ed
  ed="$(echo "$rule_json" | jq -r '.noncurrent_expiration.days // empty')"
  [[ -n "$ed" && "$age" -ge "$ed" ]]
}
