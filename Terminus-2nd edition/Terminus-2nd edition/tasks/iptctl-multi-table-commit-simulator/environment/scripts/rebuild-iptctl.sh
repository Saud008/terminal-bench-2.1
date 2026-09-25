#!/usr/bin/env bash
set -euo pipefail
for f in /app/lib/*.sh /app/scripts/iptctl; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
    chmod +x "$f"
  fi
done
