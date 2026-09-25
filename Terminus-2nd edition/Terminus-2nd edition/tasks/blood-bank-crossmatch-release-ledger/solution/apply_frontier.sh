#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

python3 <<'PY'
from pathlib import Path

panels = Path("/app/internal/panelimport/panels.go")
text = panels.read_text(encoding="utf-8")
needle = (
    "\t\tif _, err := db.Exec(`INSERT INTO patients(patient_id,abo,rh) VALUES(?,?,?)`, "
    "p.PatientID, p.ABO, p.Rh); err != nil {\n"
    "\t\t\treturn err\n"
    "\t\t}\n"
    "\t}"
)
insert = (
    "\t\tif _, err := db.Exec(`INSERT INTO patients(patient_id,abo,rh) VALUES(?,?,?)`, "
    "p.PatientID, p.ABO, p.Rh); err != nil {\n"
    "\t\t\treturn err\n"
    "\t\t}\n"
    "\t\tfor _, ab := range p.Antibodies {\n"
    "\t\t\tif _, err := db.Exec(`INSERT INTO patient_antibodies(patient_id,antibody) VALUES(?,?)`, "
    "p.PatientID, ab); err != nil {\n"
    "\t\t\t\treturn err\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t}"
)
if needle not in text:
    raise SystemExit("panels.go baseline missing patient insert block")
panels.write_text(text.replace(needle, insert, 1), encoding="utf-8")
PY

cp "${FILES_DIR}/patch_abo_rh.go" /app/internal/hemcompat/compat_matrix.go
cp "${FILES_DIR}/patch_antibody.go" /app/internal/immuno/exclusion_rules.go
cp "${FILES_DIR}/patch_expiry.go" /app/internal/shelflife/temporal_gate.go
cp "${FILES_DIR}/patch_override.go" /app/internal/emergaudit/waiver_trace.go
cp "${FILES_DIR}/patch_matrixsort.go" /app/internal/matrixstage/pair_buffer.go
cp "${FILES_DIR}/patch_emit.go" /app/internal/sealpublish/release_bundle.go

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
