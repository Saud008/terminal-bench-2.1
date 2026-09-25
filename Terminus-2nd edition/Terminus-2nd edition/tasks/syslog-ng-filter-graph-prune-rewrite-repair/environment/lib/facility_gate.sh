#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

msg_line="$1"
config_dir="$2"

filters="$(config_path "$config_dir" filters.conf)"

IFS=',' read -r msg_id facility level program host text <<<"$msg_line"

while IFS= read -r line; do
  [ -z "$line" ] && continue
  fid="${line%%|*}"
  expr="${line#*|}"
  if [[ "$expr" =~ ^facility\([a-zA-Z0-9_-]+\)$ ]]; then
    want="${expr#facility(}"
    want="${want%)}"
    if [ "$facility" = "$want" ]; then
      echo "pass"
      exit 0
    fi
  fi
done < "$filters"

echo "drop"
