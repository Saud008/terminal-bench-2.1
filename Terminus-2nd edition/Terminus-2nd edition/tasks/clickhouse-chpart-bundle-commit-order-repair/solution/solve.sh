#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/chparts-oracle.manifest" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "chparts-oracle.manifest not found" >&2; exit 1; }

while IFS=' ' read -r src dst; do
  [ -z "${src}" ] && continue
  [[ "${src}" == \#* ]] && continue
  cp -f "${SOL}/${src}" "${APP_ROOT}/${dst}"
done < "${SOL}/chparts-oracle.manifest"

cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/chparts ./cmd/chparts
test -x /usr/local/bin/chparts
bash /app/scripts/reset-state.sh
chparts read \
  --parts-dir /app/fixtures/parts \
  --config /app/config/table.json \
  --db /app/data/parts.db \
  --output /app/output/parts-report.json
