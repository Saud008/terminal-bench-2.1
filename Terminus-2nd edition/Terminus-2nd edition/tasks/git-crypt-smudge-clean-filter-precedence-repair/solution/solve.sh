#!/usr/bin/env bash
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution"; do
  if [[ -f "${candidate}/golden_gc_attrs.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_gc_attrs.sh not found" >&2; exit 1; }

for mod in gc_attrs gc_keys gc_crypto gc_staging gc_manifest; do
  sed 's/\r$//' "${SOL_DIR}/golden_${mod}.sh" > "/app/lib/${mod}.sh"
done
chmod +x /app/lib/gc_*.sh
bash /app/scripts/reset-state.sh
