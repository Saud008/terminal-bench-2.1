#!/usr/bin/env bash
set -euo pipefail

fail=0
while IFS= read -r -d '' script; do
  bash -n "$script" || fail=1
done < <(find /app/lib/roam /app/scripts -type f \( -name '*.sh' -o -name 'connman-roamctl' \) -print0)

exit "$fail"
