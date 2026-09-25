#!/usr/bin/env bash
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution"; do
  if [[ -f "${candidate}/golden_kh_parse.sh" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_kh_parse.sh not found" >&2; exit 1; }

declare -A TARGET=(
  [kh_parse]="/app/lib/parse/kh_parse.sh"
  [kh_ledger]="/app/lib/ledger/kh_ledger.sh"
  [kh_merge]="/app/lib/merge/kh_merge.sh"
  [kh_emit]="/app/lib/emit/kh_emit.sh"
  [kh_sort]="/app/lib/decoy/kh_sort_legacy.sh"
)

for mod in kh_parse kh_ledger kh_merge kh_emit kh_sort; do
  sed 's/\r$//' "${SOL_DIR}/golden_${mod}.sh" > "${TARGET[$mod]}"
done
find /app/lib -name '*.sh' -exec chmod +x {} +
bash /app/scripts/reset-state.sh
