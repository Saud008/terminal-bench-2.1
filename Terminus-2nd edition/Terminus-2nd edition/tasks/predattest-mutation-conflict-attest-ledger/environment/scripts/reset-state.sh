#!/usr/bin/env bash
# Wipe wavehold run state and published atlases between independent cases.
set -euo pipefail
rm -rf /app/state /app/output /app/work
mkdir -p /app/state/wavehold/runs /app/output /app/work
