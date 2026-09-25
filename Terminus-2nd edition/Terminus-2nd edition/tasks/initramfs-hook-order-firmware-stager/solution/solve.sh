#!/usr/bin/env bash
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "${SCRIPT_DIR}/files" "/solution" "/solution/files"; do
  if [[ -f "${candidate}/golden_irfs_scan.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_irfs_scan.sh not found" >&2; exit 1; }

declare -A TARGET=(
  [irfs_scan]="/app/lib/scan/irfs_scan.sh"
  [irfs_hooks]="/app/lib/hooks/irfs_hooks.sh"
  [irfs_modalias]="/app/lib/modalias/irfs_modalias.sh"
  [irfs_firmware]="/app/lib/firmware/irfs_firmware.sh"
  [irfs_compress]="/app/lib/compress/irfs_compress.sh"
  [irfs_ledger]="/app/lib/ledger/irfs_ledger.sh"
  [irfs_manifest]="/app/lib/manifest/irfs_manifest.sh"
  [irfs_sort_legacy]="/app/lib/decoy/irfs_sort_legacy.sh"
)

for mod in irfs_scan irfs_hooks irfs_modalias irfs_firmware irfs_compress irfs_ledger irfs_manifest irfs_sort_legacy; do
  sed 's/\r$//' "${SOL_DIR}/golden_${mod}.sh" > "${TARGET[$mod]}"
done
find /app/lib -name '*.sh' -exec chmod +x {} +
bash /app/scripts/reset-state.sh
