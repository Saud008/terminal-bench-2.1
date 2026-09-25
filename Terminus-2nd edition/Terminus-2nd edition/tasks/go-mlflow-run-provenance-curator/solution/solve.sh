#!/usr/bin/env bash
# Oracle solve - go-mlflow-run-provenance-curator
set -euo pipefail

APP="/app"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT="${SCRIPT_DIR}/patches"

install_patch() {
  local rel="$1"
  local src="${PATCH_ROOT}/${rel}"
  local dest="${APP}/internal/${rel}"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  mkdir -p "$(dirname "${dest}")"
  # Strip any CRLF that Windows checkouts may introduce.
  sed 's/\r$//' "${src}" > "${dest}"
  chmod 0644 "${dest}"
}

install_patch lineage/closure.go
install_patch digest/artifact.go
install_patch metrics/epoch.go
install_patch dataset/bind.go
install_patch staging/snapshot.go
install_patch export/summary.go

cd "${APP}"
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/mlprov ./cmd/mlprov
bash /app/scripts/reset-state.sh
test -x /usr/local/bin/mlprov
echo "mlprov oracle ready"
