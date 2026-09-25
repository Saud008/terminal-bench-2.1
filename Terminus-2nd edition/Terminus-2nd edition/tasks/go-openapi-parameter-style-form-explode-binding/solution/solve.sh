#!/usr/bin/env bash
set -euo pipefail

APP="/app"
FILES="$(cd "$(dirname "${BASH_SOURCE[0]}")/files" && pwd)"

install -d "${APP}/internal/bind"
for src in binder canonical query style validate decode emit staging publish explode_policy; do
  install -m 0644 "${FILES}/${src}.go" "${APP}/internal/bind/${src}.go"
done

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/paramgate ./cmd/paramgate
