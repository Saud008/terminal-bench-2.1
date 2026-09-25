#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/schemafit/check.go")
text = path.read_text(encoding="utf-8")
old = """\tif m.SchemaHash != expected && m.ManifestVersion != 1 {
\t\treturn fmt.Errorf("schema mismatch for %s", m.OperationID)
\t}
\tif m.ManifestVersion != 1 {
\t\treturn fmt.Errorf("schema mismatch for %s", m.OperationID)
\t}"""
new = """\tif m.SchemaHash != expected {
\t\treturn fmt.Errorf("schema mismatch for %s", m.OperationID)
\t}
\tif m.ManifestVersion != 1 {
\t\treturn fmt.Errorf("unsupported manifest version for %s", m.OperationID)
\t}"""
if old not in text:
    raise SystemExit("schemafit anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
