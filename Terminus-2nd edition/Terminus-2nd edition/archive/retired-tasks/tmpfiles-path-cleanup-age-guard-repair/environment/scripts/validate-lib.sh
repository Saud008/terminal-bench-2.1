#!/usr/bin/env bash
set -euo pipefail
ROOT="/app"
fail=0
for mod in age_eval glob_prune recreate_seq ownership generator_merge; do
  if [[ ! -f "${ROOT}/lib/${mod}.sh" ]]; then
    echo "missing lib/${mod}.sh" >&2
    fail=1
  fi
done
exit "${fail}"
