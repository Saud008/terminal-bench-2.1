#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_ROOT=""

for candidate in "${SCRIPT_DIR}/files" "/solution/files" "/oracle/solution/files" "/task/solution/files"; do
  if [[ -f "${candidate}/statusmap_contract.go" ]]; then
    FILES_ROOT="${candidate}"
    break
  fi
done

if [[ -z "${FILES_ROOT}" ]]; then
  echo "oracle: statusmap_contract.go not found under solution/files" >&2
  exit 1
fi

python3 "${SCRIPT_DIR}/apply_modules.py" --files-root "${FILES_ROOT}" --app-root "${APP_ROOT}"

cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/grpcfaultd ./cmd/grpcfaultd
"${APP_ROOT}/scripts/reset-state.sh"
