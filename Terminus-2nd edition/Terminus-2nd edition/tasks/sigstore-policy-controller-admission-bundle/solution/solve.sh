#!/usr/bin/env bash
# Reference oracle: applies the corrected package files over the buggy
# shipped baseline, rebuilds slsacip, resets staged state/output, and runs
# the attest command against the wave-north pull-wave fixture.
set -euo pipefail

APP="/app"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${SOL}/files"

cp -f "${FILES}/oracle_rootbind.go"     "${APP}/cipkernel/rootbind/glob.go"
cp -f "${FILES}/oracle_pindeny.go"      "${APP}/cipkernel/pindeny/deny.go"
cp -f "${FILES}/oracle_revokewin.go"    "${APP}/cipkernel/revokewin/window.go"
cp -f "${FILES}/oracle_predallow.go"    "${APP}/cipkernel/predallow/allow.go"
cp -f "${FILES}/oracle_buildergate.go"  "${APP}/cipkernel/buildergate/gate.go"
cp -f "${FILES}/oracle_quorumadmit.go"  "${APP}/cipkernel/quorumadmit/evaluate.go"
cp -f "${FILES}/oracle_witnesswrite.go" "${APP}/cipkernel/witnesswrite/snapshot.go"
cp -f "${FILES}/oracle_sealhex.go"      "${APP}/cipkernel/sealhex/audit.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=mod -o /usr/local/bin/slsacip ./cmd/slsacip

bash "${APP}/scripts/reset-state.sh"

slsacip attest \
  --config /app/config/slsacip.json \
  --pulls  /app/fixtures/pull-waves/wave-north.jsonl \
  --output /app/output/slsa-admission-ledger.json
