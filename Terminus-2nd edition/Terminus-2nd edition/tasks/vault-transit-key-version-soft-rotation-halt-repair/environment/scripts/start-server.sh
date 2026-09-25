#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
pkill -f '/usr/local/bin/transit-mock' 2>/dev/null || true
sleep 0.2
/usr/local/bin/transit-mock >/tmp/transit-mock.log 2>&1 &
for _ in $(seq 1 50); do
  if curl -sf http://127.0.0.1:8200/healthz >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.1
done
echo "transit-mock failed to start" >&2
cat /tmp/transit-mock.log >&2 || true
exit 1
