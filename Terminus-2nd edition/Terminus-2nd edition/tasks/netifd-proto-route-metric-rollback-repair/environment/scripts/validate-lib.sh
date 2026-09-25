#!/usr/bin/env bash
set -euo pipefail
missing=0
for f in /app/lib/netifd/common.sh /app/lib/netifd/proto.sh /app/lib/netifd/export.sh; do
  [[ -f "$f" ]] || { echo "missing $f" >&2; missing=1; }
done
exit "$missing"
