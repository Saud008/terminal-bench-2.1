#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution/files"; do
  if [ -f "${candidate}/golden_canon.py" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_canon.py not found" >&2; exit 1; }

mkdir -p /app/lib/party

for module in canon ledger stage publish sweeper query; do
  cp -f "${SOL}/golden_${module}.py" "/app/lib/party/${module}.py"
done

for copied in /app/lib/party/*.py; do
  sed -i 's/\r$//' "${copied}"
done

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh

test -x /app/bin/partyd
echo "party-audit-governor oracle ready"
