#!/usr/bin/env bash
set -euo pipefail

# Preflight checks for verifier rebuild path.
command -v gawk >/dev/null
command -v sqlite3 >/dev/null
test -x /app/bin/rspamd-fuzzy-audit

shopt -s nullglob
for f in /app/bin/rspamd-fuzzy-audit /app/scripts/*.sh /app/lib/rspamd/*.sh \
  /app/lib/rspamd/snapshot/*.sh /app/lib/rspamd/summary/*.sh \
  /app/lib/rspamd/corpus/*.sh /app/lib/rspamd/decoy/*.sh; do
  bash -n "$f"
done
