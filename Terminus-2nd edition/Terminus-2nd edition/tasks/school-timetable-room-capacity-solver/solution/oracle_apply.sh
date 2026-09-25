#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${ROOT_DIR}/patches"

install -m 0644 "${PATCHES}/patch_sectioncohort.go" /app/internal/sectioncohort/sync.go
install -m 0644 "${PATCHES}/patch_teacherlock.go" /app/internal/policycheck/teacherlock.go
install -m 0644 "${PATCHES}/patch_roomcap.go" /app/internal/policycheck/roomcap.go
install -m 0644 "${PATCHES}/patch_labfit.go" /app/internal/policycheck/labfit.go
install -m 0644 "${PATCHES}/patch_rankkey.go" /app/internal/rankkey/score.go
install -m 0644 "${PATCHES}/patch_constraintgraph.go" /app/internal/constraintgraph/writer.go
install -m 0644 "${PATCHES}/patch_conflictpub.go" /app/internal/conflictpub/emit.go
install -m 0644 "${PATCHES}/patch_slotplan.go" /app/internal/slotplan/solve.go

python3 - <<'PY'
from pathlib import Path

path = Path("/app/internal/timetablepub/publish.go")
text = path.read_text(encoding="utf-8")
needle = 'if allocgate.AllocationPass() <= 0'
if needle in text:
    raise SystemExit(0)
if '"fmt"' not in text:
    text = text.replace('"encoding/json"\n', '"encoding/json"\n    "fmt"\n')
text = text.replace(
    "    _ = allocgate.AllocationPass()",
    '    if allocgate.AllocationPass() <= 0 {\n        return fmt.Errorf("publish-atlas: allocation_pass is zero")\n    }',
)
path.write_text(text, encoding="utf-8")
PY

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
