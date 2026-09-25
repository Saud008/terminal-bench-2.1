#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution"; do
  if [ -f "${candidate}/internal/ingest/ingest.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "solution ingest.go not found" >&2; exit 1; }

cp -f "${SOL}/internal/ingest/ingest.go" /app/internal/ingest/ingest.go
cp -f "${SOL}/internal/globexpand/expand.go" /app/internal/globexpand/expand.go
cp -f "${SOL}/internal/digest/normalize.go" /app/internal/digest/normalize.go
cp -f "${SOL}/internal/lineage/hash.go" /app/internal/lineage/hash.go
cp -f "${SOL}/internal/audit/rules.go" /app/internal/audit/rules.go
cp -f "${SOL}/internal/audit/provenance.go" /app/internal/audit/provenance.go
cp -f "${SOL}/internal/export/report.go" /app/internal/export/report.go

for copied in \
  /app/internal/ingest/ingest.go \
  /app/internal/globexpand/expand.go \
  /app/internal/digest/normalize.go \
  /app/internal/lineage/hash.go \
  /app/internal/audit/rules.go \
  /app/internal/audit/provenance.go \
  /app/internal/export/report.go; do
  sed -i 's/\r$//' "${copied}"
done

go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/nfresume-audit ./cmd/nfresume-audit
test -x /app/bin/nfresume-audit

# Demonstrate a full oracle pass: ingest -> audit -> export for every bundled scenario.
bash /app/scripts/reset-state.sh
SEED="alpha"
SCENARIOS=(
  clean-pipeline
  digest-drift
  glob-mismatch
  retry-stale
  provenance-crossrun
  lineage-break
)
for scenario in "${SCENARIOS[@]}"; do
  # Preserve sealed reports across scenarios (reset-state clears /app/output).
  rm -rf /app/state/* /app/work/*
  mkdir -p /app/state /app/work /app/output
  echo '{"audit_generation":0}' > /app/state/audit-generation.json

  /app/bin/nfresume-audit ingest --seed "${SEED}" --scenario "${scenario}" --fixture-dir /app/fixtures
  /app/bin/nfresume-audit audit --scenario "${scenario}"
  out="/app/output/${SEED}-${scenario}-report.json"
  /app/bin/nfresume-audit export --scenario "${scenario}" --output "${out}"
  test -s /app/state/resume-stage.json
  test -s /app/work/audit-findings.json
  test -s /app/state/audit-generation.json
  test -s "${out}"
done

echo "nextflow-channel-resume-cache-auditor oracle ready"
