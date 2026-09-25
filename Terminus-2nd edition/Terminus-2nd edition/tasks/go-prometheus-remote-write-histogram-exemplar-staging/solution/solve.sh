#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
APP_ROOT="${APP_ROOT:-/app}"
cd "${APP_ROOT}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_staging.go" ]] || [[ -f "${candidate}/internal/staging/persist.go" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [[ -z "${SOL_DIR}" ]]; then
  echo "oracle: solution files not found" >&2
  exit 1
fi

if [[ -f "${SOL_DIR}/internal/ingest/decode.go" ]]; then
  cp -f "${SOL_DIR}/internal/ingest/decode.go" "${APP_ROOT}/internal/ingest/decode.go"
  cp -f "${SOL_DIR}/internal/exemplar/bind.go" "${APP_ROOT}/internal/exemplar/bind.go"
  cp -f "${SOL_DIR}/internal/relabel/relabel.go" "${APP_ROOT}/internal/relabel/relabel.go"
  cp -f "${SOL_DIR}/internal/staging/persist.go" "${APP_ROOT}/internal/staging/persist.go"
  cp -f "${SOL_DIR}/internal/server/server.go" "${APP_ROOT}/internal/server/server.go"
else
  cp -f "${SOL_DIR}/golden_decode.go" "${APP_ROOT}/internal/ingest/decode.go"
  cp -f "${SOL_DIR}/golden_bind.go" "${APP_ROOT}/internal/exemplar/bind.go"
  cp -f "${SOL_DIR}/golden_relabel.go" "${APP_ROOT}/internal/relabel/relabel.go"
  cp -f "${SOL_DIR}/golden_staging.go" "${APP_ROOT}/internal/staging/persist.go"
  cp -f "${SOL_DIR}/golden_server.go" "${APP_ROOT}/internal/server/server.go"
fi

go build -mod=readonly -o /usr/local/bin/promingest ./cmd/promingest
go build -mod=readonly -o /usr/local/bin/promenc ./cmd/promenc
bash "${APP_ROOT}/scripts/reset-state.sh"
