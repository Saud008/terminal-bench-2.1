#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${SOL}/files"

cp -f "${FILES}/golden_build.go" "${APP}/internal/graph/build.go"
cp -f "${FILES}/golden_topo.go" "${APP}/internal/graph/topo.go"
cp -f "${FILES}/golden_serialize.go" "${APP}/internal/export/serialize.go"
cp -f "${FILES}/golden_ledger.go" "${APP}/internal/graph/ledger.go"
cp -f "${FILES}/golden_validate.go" "${APP}/internal/validate/snapshot.go"
cp -f "${FILES}/golden_replay.go" "${APP}/internal/replay/order.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/pulumi-dep-export ./cmd/pulumi-dep-export

bash "${APP}/scripts/reset-state.sh"
pulumi-dep-export order \
  --stack /app/fixtures/stacks/07-merged.json \
  --output /app/output/pulumi-export-order.json
