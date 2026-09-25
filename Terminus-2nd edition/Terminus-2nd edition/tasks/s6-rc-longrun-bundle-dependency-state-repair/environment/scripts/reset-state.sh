#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/* /app/state/rc /app/state/staging.json /app/state/applied.json /app/state/transition-log.json
mkdir -p /app/output /app/state/rc
: > /app/output/.parser-touch
