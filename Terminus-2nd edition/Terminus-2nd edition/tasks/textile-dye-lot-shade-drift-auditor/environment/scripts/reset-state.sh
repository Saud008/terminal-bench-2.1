#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/shade-correlation /app/work/tb3-root
mkdir -p /app/state/shade-correlation /app/work /app/output
: > /app/state/run-registry.jsonl
