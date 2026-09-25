#!/usr/bin/env bash
set -uo pipefail

mkdir -p /app/output
setsid /usr/local/bin/grpcfaultd --listen 127.0.0.1:50051 >>/app/output/grpcfaultd.log 2>&1 &
echo $! >/app/output/grpcfaultd.pid

for _ in $(seq 1 50); do
  if /usr/local/bin/grpcurl -plaintext 127.0.0.1:50051 list 2>/dev/null | grep -q fault.v1.Admin; then
    exit 0
  fi
  sleep 0.3
done

cat /app/output/grpcfaultd.log >&2 || true
echo "grpcfaultd failed to become ready" >&2
exit 1
