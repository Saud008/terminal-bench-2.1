#!/usr/bin/env bash
set -euo pipefail
pkill -x paramgate 2>/dev/null || true
sleep 0.2
/usr/local/bin/paramgate >/dev/null 2>&1 &
disown
sleep 0.4
