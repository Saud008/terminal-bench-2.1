#!/usr/bin/env bash
set -euo pipefail
for f in /app/lib/*.sh; do
  bash -n "$f"
done
test -x /app/bin/monitctl
