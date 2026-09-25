#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT=""
for candidate in "${SCRIPT_DIR}/files/internal" "/solution/files/internal" "/oracle/solution/files/internal"; do
  if [ -f "${candidate}/archive/writer.go" ]; then
    PATCH_ROOT="${candidate}"
    break
  fi
done
[[ -n "${PATCH_ROOT}" ]] || { echo "oracle patch root not found" >&2; exit 1; }

install_patch() {
  local rel="$1"
  local src="${PATCH_ROOT}/${rel}"
  local dest="/app/internal/${rel}"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  mkdir -p "$(dirname "${dest}")"
  cp -f "${src}" "${dest}"
  sed -i 's/\r$//' "${dest}"
}

install_patch archive/writer.go
install_patch restore/import.go
install_patch retention/purge.go
install_patch export/publish.go
install_patch staging/snapshot.go

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/archctl
echo "asynq-archive oracle ready"
