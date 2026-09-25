#!/usr/bin/env bash
set -euo pipefail

command -v gawk >/dev/null
command -v sqlite3 >/dev/null
test -x /app/bin/offlineimap-audit

for f in /app/bin/offlineimap-audit /app/scripts/*.sh /app/lib/offlineimap/*.sh \
  /app/lib/offlineimap/staging/*.sh /app/lib/offlineimap/export/*.sh; do
  bash -n "$f"
done
