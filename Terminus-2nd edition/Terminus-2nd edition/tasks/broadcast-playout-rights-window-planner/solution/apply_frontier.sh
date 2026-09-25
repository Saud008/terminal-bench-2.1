#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/files"

test -d "${FILES}"
test -f "${FILES}/grid_overlap.go"
test -f "${FILES}/grid_sqlite.go"
test -f "${FILES}/grid_stage.go"

cp "${FILES}/grid_overlap.go" /app/internal/windowpick/overlap.go
test -s /app/internal/windowpick/overlap.go
cp "${FILES}/grid_precede.go" /app/internal/darkregion/precede.go
test -s /app/internal/darkregion/precede.go
cp "${FILES}/grid_keep.go" /app/internal/breakcue/keep.go
test -s /app/internal/breakcue/keep.go
cp "${FILES}/grid_map.go" /app/internal/lineswap/subst.go
test -s /app/internal/lineswap/subst.go
cp "${FILES}/grid_sqlite.go" /app/internal/plannerdb/sqlite.go
test -s /app/internal/plannerdb/sqlite.go
cp "${FILES}/grid_stage.go" /app/internal/runwaysnap/stage.go
test -s /app/internal/runwaysnap/stage.go
cp "${FILES}/grid_gate.go" /app/internal/syndemit/gate.go
test -s /app/internal/syndemit/gate.go
cp "${FILES}/grid_conflicts.go" /app/internal/syndemit/conflicts.go
test -s /app/internal/syndemit/conflicts.go
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
