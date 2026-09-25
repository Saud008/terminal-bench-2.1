#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

cp "${ROOT_DIR}/files/oracle_snapgraph_ancestry.go" /app/internal/snapgraph/ancestry.go
cp "${ROOT_DIR}/files/oracle_manifestreach_reach.go" /app/internal/manifestreach/reach.go
cp "${ROOT_DIR}/files/oracle_deletefile_retention.go" /app/internal/deletefile/retention.go
cp "${ROOT_DIR}/files/oracle_branchtag_protect.go" /app/internal/branchtag/protect.go
cp "${ROOT_DIR}/files/oracle_orphan_account.go" /app/internal/orphan/account.go
cp "${ROOT_DIR}/files/oracle_planemit_plan.go" /app/internal/planemit/plan.go
cp "${ROOT_DIR}/files/oracle_cursorsnap_stage.go" /app/internal/cursorsnap/stage.go
cp "${ROOT_DIR}/files/oracle_catalogload_loadtable.go" /app/internal/catalogload/loadtable.go

sed -i 's/gen.AnalyzeRevision = gen.AnalyzeRevision$/gen.AnalyzeRevision = gen.AnalyzeRevision + 1/' \
  /app/internal/analyzepass/core.go
