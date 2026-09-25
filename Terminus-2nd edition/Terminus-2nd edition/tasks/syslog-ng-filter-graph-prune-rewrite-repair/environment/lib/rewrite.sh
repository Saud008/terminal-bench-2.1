#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

msg_line="$1"
config_dir="$2"

filters="$(config_path "$config_dir" filters.conf)"
rewrites="$(config_path "$config_dir" rewrites.conf)"

IFS=',' read -r msg_id facility level program host text <<<"$msg_line"

applied=0
while IFS='|' read -r rw_id filter_ref template; do
  [ -z "$rw_id" ] && continue
  if bash /app/lib/boolean.sh "$msg_line" "$filters" "$filter_ref"; then
    program="${template}${program}"
    applied=1
  fi
done < "$rewrites"

echo "${msg_id},${facility},${level},${program},${host},${text}|${applied}"
