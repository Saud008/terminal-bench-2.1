#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

bash "${ROOT_DIR}/patch_manifestload.sh"
bash "${ROOT_DIR}/patch_schemafit.sh"
bash "${ROOT_DIR}/patch_tenantquota.sh"
bash "${ROOT_DIR}/patch_expiryevict.sh"
bash "${ROOT_DIR}/patch_ledgerreconcile.sh"

cp "${ROOT_DIR}/files/gql_oracle_stagefreeze.go" /app/internal/stagefreeze/write.go
cp "${ROOT_DIR}/files/gql_oracle_auditexport.go" /app/internal/auditexport/sqlite.go
