#!/usr/bin/env bash
# Re-link the wavehold CLI and refresh the compiled gate bytecode before a
# preview run. Safe to run repeatedly; it performs no wave processing.
set -euo pipefail
mkdir -p /app/bin
ln -sf /app/scripts/wavehold /app/bin/wavehold
chmod +x /app/scripts/wavehold /app/scripts/reset-state.sh
find /app/lib -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
python3 -c "import compileall; compileall.compile_dir('/app/lib', quiet=1)" || true
