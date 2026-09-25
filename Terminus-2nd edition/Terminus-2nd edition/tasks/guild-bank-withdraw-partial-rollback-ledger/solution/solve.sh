#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_dao.go" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_dao.go not found" >&2
  exit 1
fi

cd "${APP_ROOT}"
cp -f "${SOL_DIR}/golden_store.go" internal/store/store.go
cp -f "${SOL_DIR}/golden_dao.go" internal/bank/dao.go
cp -f "${SOL_DIR}/golden_withdraw.go" internal/bank/withdraw.go
cp -f "${SOL_DIR}/golden_transfer.go" internal/bank/transfer.go
cp -f "${SOL_DIR}/golden_accrual.go" internal/interest/accrual.go

for f in internal/store/store.go internal/bank/dao.go internal/bank/withdraw.go \
  internal/bank/transfer.go internal/interest/accrual.go; do
  sed -i 's/\r$//' "$f" 2>/dev/null || true
done

bash /app/scripts/verifier-rebuild.sh
test -x /usr/local/bin/guildbankd
