#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
path = Path("/app/internal/codealias/alias_resolve.go")
text = path.read_text(encoding="utf-8")
old = """func NormalizeProject(input string, aliases map[string]string) string {
\t_ = aliases
\treturn input
}"""
new = """func NormalizeProject(input string, aliases map[string]string) string {
\tcur := input
\tseen := map[string]struct{}{}
\tfor {
\t\tif _, ok := seen[cur]; ok {
\t\t\tbreak
\t\t}
\t\tseen[cur] = struct{}{}
\t\ttarget, ok := aliases[cur]
\t\tif !ok || target == \"\" || target == cur {
\t\t\tbreak
\t\t}
\t\tcur = target
\t}
\treturn cur
}"""
if old not in text:
    raise SystemExit("codealias anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
