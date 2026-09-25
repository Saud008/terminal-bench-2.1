#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

python3 <<'PY'
from pathlib import Path

bindres = Path("/app/internal/bindres/residuals.go")
text = bindres.read_text(encoding="utf-8")
old = "\t\t_ = qmask.Exclude(star.DetMask, star.CatMask)\n"
new = "\t\tif qmask.Exclude(star.DetMask, star.CatMask) {\n\t\t\tcontinue\n\t\t}\n"
if old not in text:
    raise SystemExit("bindres baseline missing mask noop")
bindres.write_text(text.replace(old, new, 1), encoding="utf-8")

flow = Path("/app/internal/orchestrate/flow.go")
ftext = flow.read_text(encoding="utf-8")
needle = "\tcase \"seal-closure\":\n\t\tbody, err := sealcert.Certificate(id, rows)"
insert = (
    "\tcase \"seal-closure\":\n"
    "\t\tif persist.BindPass() <= 0 {\n"
    "\t\t\treturn fmt.Errorf(\"bind pass required before seal-closure\")\n"
    "\t\t}\n"
    "\t\tbody, err := sealcert.Certificate(id, rows)"
)
if needle not in ftext:
    raise SystemExit("orchestrate baseline missing seal branch")
flow.write_text(ftext.replace(needle, insert, 1), encoding="utf-8")
PY

cp "${FILES_DIR}/cardlex/parse.go" /app/internal/cardlex/parse.go
cp "${FILES_DIR}/wcsmatrix/extract.go" /app/internal/wcsmatrix/extract.go
cp "${FILES_DIR}/tanproj/project.go" /app/internal/tanproj/project.go
cp "${FILES_DIR}/epochnudge/nudge.go" /app/internal/epochnudge/nudge.go
cp "${FILES_DIR}/qmask/gate.go" /app/internal/qmask/gate.go
cp "${FILES_DIR}/sealcert/certificate.go" /app/internal/sealcert/certificate.go

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
