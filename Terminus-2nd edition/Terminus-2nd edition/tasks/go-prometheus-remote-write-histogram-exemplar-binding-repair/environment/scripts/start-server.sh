#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
PIDFILE=/app/output/promingest.pid
if [[ -f "${PIDFILE}" ]]; then
  kill "$(cat "${PIDFILE}")" 2>/dev/null || true
  rm -f "${PIDFILE}"
fi
setsid /usr/local/bin/promingest --listen 127.0.0.1:9090 >/app/output/promingest.log 2>&1 &
echo $! > "${PIDFILE}"
for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:9090/healthz" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.25
done
echo "promingest failed readiness" >&2
exit 1
