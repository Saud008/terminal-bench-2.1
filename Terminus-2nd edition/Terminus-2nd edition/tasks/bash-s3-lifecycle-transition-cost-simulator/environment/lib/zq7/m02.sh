#!/usr/bin/env bash
set -euo pipefail
S3LC_LIB="${S3LC_LIB:-/app/lib}"
source "${S3LC_LIB}/zq7/m01.sh"

pick_winning_rule() {
  local tags_json="$1" rules_json="$2"
  local winner="" win_pri=999999 win_spec=-1
  local id pri spec tags prefixes row
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    id="$(echo "$row" | jq -r '.id')"
    pri="$(echo "$row" | jq -r '.priority')"
    prefixes="$(echo "$row" | jq -c '.tag_prefixes')"
    tags="$tags_json"
    if tag_prefixes_match "$tags" "$prefixes"; then
      spec="$(echo "$prefixes" | jq 'length')"
      if [[ -z "$winner" || "$pri" -lt "$win_pri" || ( "$pri" -eq "$win_pri" && "$spec" -gt "$win_spec" ) ]]; then
        winner="$row"
        win_pri="$pri"
        win_spec="$spec"
      elif [[ "$pri" -eq "$win_pri" && "$spec" -eq "$win_spec" ]]; then
        local wid
        wid="$(echo "$winner" | jq -r '.id')"
        [[ "$id" < "$wid" ]] && winner="$row"
      fi
    fi
  done < <(echo "$rules_json" | jq -c '.rules[]')
  echo "$winner"
}
