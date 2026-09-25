#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state /app/work /app/output
mkdir -p /app/state/ /app/work/residual-matrix /app/output
printf '%s\n' '{"bind_pass":0}' > /app/state/bind-pass.json
